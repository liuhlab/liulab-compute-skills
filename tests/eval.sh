#!/usr/bin/env bash
# Layer 3 — agent evals: run the skills through real headless Claude Code
# sessions and assert on the behavior they induce. COSTS TOKENS (one full
# claude -p session per case) and several minutes of wall time.
#
# THERE IS NO DEFAULT RUN. A bare `eval.sh` prints the case list and exits 2
# without launching anything. Spending has to be asked for by name — `--only
# <case>` for one, `--all` for the suite — because the failure mode this guards
# is an agent running the whole thing on a hunch, repeatedly, on someone else's
# budget. `--live` on its own is refused for the same reason: it is a modifier,
# not a request.
#
# Agents/automation: prefer `--only <case>`, and ASK the user before `--all` or
# anything live (touches the real cluster and spends an Edison credit). Cases run
# CONCURRENTLY, so a suite's wall time is roughly the slowest single case.
#
# NOTE: evals exercise the INSTALLED plugin (plugin cache), not this working
# tree — push + `claude plugin update lab-compute@liulab` first, or results
# reflect the previous version.
#
# Usage: eval.sh --only <case> | --all [--live] | --dump
#   --only <case>  run one case, and nothing else
#                  (trigger|explicit|reject|containers|jupyter-ircbc|reuse-job|
#                   edison-refuse|edison-molecules|edison-kosmos|edison-recover|
#                   live-sbatch|live-edison)
#                  Any `live-*` case implies --live, so naming one is enough.
#   --all          run every non-live case. Add --live for the two end-to-end
#                  cases as well: a tiny hostname job submitted and cleaned up on
#                  arc, and one real Edison literature call that spends one of
#                  the user's platform credits.
#   --dump         print each case's assertions and exit; runs nothing, spends
#                  nothing. This is what `tests/lint.sh` reads.
#
# Assertions are loose key-phrase greps: evals are non-deterministic. On
# failure, read the saved transcript before concluding the skill is broken.
set -u
# `|| exit 1`: the cases below are written against the repo root, and a run that spends
# tokens from the wrong directory is worse than one that never starts.
cd "$(dirname "$0")/.." || exit 1

CASES="trigger explicit reject containers jupyter-ircbc reuse-job edison-refuse edison-molecules edison-kosmos edison-recover live-sbatch live-edison"

# Refuse, and say what to type instead. Exit 2 — the same code an unknown flag gets,
# because both mean "this invocation asked for nothing runnable", and neither is a
# failing eval (exit 1). A caller that treats 2 as a red suite has misread it.
refuse() { # <why>
  echo "eval.sh: $1" >&2
  echo >&2
  echo "Nothing was run and nothing was spent. Every case is a real headless agent" >&2
  echo "session, so a run has to be asked for by name:" >&2
  echo >&2
  echo "  bash tests/eval.sh --only <case>   one case" >&2
  echo "  bash tests/eval.sh --all           every non-live case" >&2
  echo "  bash tests/eval.sh --all --live    the suite, including the cluster job" >&2
  echo "                                     and one real Edison credit" >&2
  echo >&2
  echo "cases: $CASES" >&2
  exit 2
}

LIVE=false ONLY="" DUMP=false ALL=false
while [ $# -gt 0 ]; do
  case "$1" in
    # A modifier, never a request. On its own it used to mean "the whole suite plus the
    # expensive two", which is the most costly thing this script can do and the shortest
    # thing to type — so it now needs --all or a named live case beside it.
    --live) LIVE=true ;;
    # The explicit opt-in to the whole suite. There is deliberately no short form.
    --all) ALL=true ;;
    # Print each case's name and its two assertions, run nothing, spend nothing. This is
    # what lets `tests/lint.sh` test the regexes against fixture transcripts without an
    # API call — and test THESE regexes, not a copy of them that would drift.
    --dump) DUMP=true; LIVE=true; ALL=true ;;
    # Every live case is named `live-*`, so asking for one by name turns --live on.
    # Without this, `--only live-<x>` would report "no cases matched" and spend nothing.
    --only) shift; [ $# -gt 0 ] || refuse "--only needs a case name"; ONLY="$1"; case "$ONLY" in live-*) LIVE=true ;; esac ;;
    *) echo "unknown arg: $1" >&2; refuse "unknown argument" ;;
  esac
  shift
done

# The guard. Checked after parsing, not during, so `--live --all` and `--all --live` are
# the same invocation and neither order is a trap.
if [ -z "$ONLY" ] && ! $ALL; then
  if $LIVE; then refuse "--live is a modifier, not a request — pass --all --live, or name a live case"
  else refuse "no case selected"; fi
fi
# A named case is exactly one case, so --all beside it is a contradiction: one of the two
# is a typo, and guessing which would spend the budget the guess got wrong.
if [ -n "$ONLY" ] && $ALL && ! $DUMP; then
  refuse "--only and --all contradict each other — pass one"
fi
if [ -n "$ONLY" ]; then
  case " $CASES " in *" $ONLY "*) ;; *) refuse "no such case: $ONLY" ;; esac
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/lab-skill-eval.XXXXXX")
if ! $DUMP; then
  # Say what is about to be spent, before it is. The guard above stops an accidental run;
  # this line stops a deliberate one that meant something smaller.
  if [ -n "$ONLY" ]; then echo "running 1 case: $ONLY"
  elif $LIVE; then echo "running EVERY case, including live: a real Slurm job on arc and one Edison credit"
  else echo "running every non-live case (9 headless agent sessions)"; fi
  echo "transcripts: $tmp"
fi

declare -a E_NAME E_EXPECT E_DENY E_PID

# Set DENY on the line before a launch_eval call to give that one case a second,
# NEGATIVE assertion: the transcript must not match this pattern. One regex cannot
# say "contains this and not that", and the Edison case needs both — a refusal that
# then asks for the key in chat is the failure the case exists to catch. The call
# consumes DENY, so it can never leak into the next case.
DENY=""

# A `--permission-mode plan` session may write its answer to a plan file and print only a
# one-line pointer to it. Stdout then greps as an empty answer and a CORRECT run fails —
# observed on `edison-molecules`, whose plan routed to MOLECULES and warned off the retired
# job while stdout said nothing but "the plan is written to ...". Which way a session goes
# is not deterministic, so this is a latent false FAIL under all seven plan-mode cases, not
# a quirk of one. Fold any plan file the transcript names back into the transcript before
# asserting. Both assertions then read it, which is what we want: a DENY has to see the
# plan too, or a plan that quietly submits would pass by being written down instead of said.
fold_plans() { # <transcript>
  local t="$1" pf
  grep -oE '/[^[:space:]"'"'"'`]+/plans/[^[:space:]"'"'"'`]+\.md' "$t" | sort -u |
  while IFS= read -r pf; do
    [ -f "$pf" ] || continue
    { printf '\n--- plan file %s ---\n' "$pf"; cat "$pf"; } >>"$t"
  done
}

launch_eval() { # <name> <expected-regex> <prompt> [extra claude flags...]
  local name="$1" expect="$2" prompt="$3"; shift 3
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && { DENY=""; return 0; }
  if $DUMP; then printf '%s\t%s\t%s\n' "$name" "$expect" "$DENY"; DENY=""; return 0; fi
  echo "-- $name: launched"
  # NOTE: prompt must precede flags — variadic flags (--allowedTools) would
  # otherwise swallow it.
  claude -p "$prompt" "$@" >"$tmp/$name.txt" 2>&1 &
  E_NAME+=("$name"); E_EXPECT+=("$expect"); E_DENY+=("$DENY"); E_PID+=($!)
  DENY=""
}

# 1. Auto-trigger: HPC-flavored prompt, skill never named, plan mode (no
#    execution). Expect a Slurm-first plan, not naive ssh-and-run.
launch_eval trigger 'slurm|sbatch|salloc|squeue|compute node' \
  "get me a GPU node on chimera and pull the latest liulab-runtime there" \
  --permission-mode plan

# 2. Explicit invocation of the plugin skill.
launch_eval explicit 'login node' \
  "/lab-compute:lab-hpc state the skill's hard safety rules in at most 3 bullets, do nothing else"

# 3. Clear rejection when the machine is not configured: the agent is told
#    the preflight failed and must refuse rather than improvise. (No
#    'missing' in the regex — the prompt itself contains that word, so an
#    improvising agent would match it too. grep -i makes a separate
#    'NOT CONFIGURED' alternate redundant.)
launch_eval reject 'not (set up|configured)|refus' \
  "Suppose the lab-hpc preflight (scripts/check-hpc-config.sh) just reported: 'arc_hpc: NOT CONFIGURED (missing: arc chimera-login)'. My request: get me a GPU node on chimera. What do you do?" \
  --permission-mode plan

# 4. Recipe skill triggers: image build request must surface the
#    lab-containers pull-on-login / build-in-compute-job procedure. (Only
#    recipe-unique terms — 'sbatch'/'login node' would also match a naive
#    singularity-pull-on-a-node plan.)
launch_eval containers 'crane|docker-archive' \
  "rebuild the align-rna singularity image on ircbc" \
  --permission-mode plan

# 5. Cross-skill seam: Jupyter on ircbc must plan the container path, not
#    the arc-native flow. (Container-unique terms only — 'squeue -u' or a
#    bare 'sif' substring would also match a wrong arc-style plan.)
launch_eval jupyter-ircbc 'singularity|\.sif|liulab-runtime|compute_cpu|lab-containers' \
  "start jupyter lab on ircbc and tunnel it to my laptop" \
  --permission-mode plan

# 6. Reuse-idle-job: with a job already held, running work must reuse that
#    node, not `ssh arc "<work>"` on the login node. (Reuse-unique terms
#    only — a bare 'squeue' would also match a naive check-then-ssh-login
#    plan, so require the reuse/idle/existing-job vocabulary.)
#    'foothold', 'holding your job' and 'no new allocation' were added after
#    2026.9.0: the skill now frames this as taking a foothold, and a correct
#    plan phrased that way was failing an assertion that only knew the older
#    'reuse an idle job' wording. All the alternates stay reuse-specific.
launch_eval reuse-job 'reuse|idle|foothold|existing (interactive )?job|already (running|holds|have)|node it holds|holding (your|the|a) job|no new allocation' \
  "I already keep an interactive GPU job running on arc. Run my repo's train.py on the cluster." \
  --permission-mode plan

# 7. Edison refusal: with no key on the machine, the skill must refuse and offer
#    to create the key file — and must never ask for the key in the chat, which
#    would put a credential in the transcript. The preflight verdict is supplied
#    in the prompt, as case 3 does, because whether THIS machine has an Edison
#    key is not something the case may depend on. The prompt carries none of the
#    words asserted on, so only the skill can produce them. `lab-edison` is
#    user-invoked only, hence the slash command.
DENY="what('s| is) your[^.]{0,30}key|(paste|type|enter|send|share|provide) your[^.]{0,30}key (here|in (this|the) (chat|conversation|message))"
launch_eval edison-refuse 'refus|not configured|edison\.env|chmod 600' \
  "/lab-compute:lab-edison Suppose the Edison preflight just reported 'key file: MISSING' and exited 1 on this machine. My request: find recent literature on m6A readers using Edison. What do you do? Run nothing." \
  --permission-mode plan

# 8. Edison routing, chemistry: the request must reach the current molecules job.
#    The retired alias is the trap — the package returns 404 for new submissions
#    against it — so this case carries a DENY as well. The DENY matches the retired
#    JOB VALUE and the qualified member, not the bare word: a correct answer may well
#    name the retired member while warning about it, and the value string appears
#    nowhere in this repo, so a transcript holding it came from the model, not the
#    skill. The prompt says "compound" and never "molecule", so only the skill can
#    produce the asserted name. The preflight verdict is supplied as in cases 3 and 7:
#    whether THIS machine holds an Edison key must not decide the result.
DENY="job-futurehouse-phoenix|JobNames\.PHOENIX"
launch_eval edison-molecules 'MOLECULES|data-analysis-molecules' \
  "/lab-compute:lab-edison Suppose the Edison preflight just reported 'edison: CONFIGURED' and exited 0. I want to ask Edison about the predicted properties and a plausible synthesis route for a small drug-like compound. Which job would you submit that to, and what would you show me before submitting? Plan only, run nothing." \
  --permission-mode plan

# 9. Edison Kosmos: the request must be answered with what Kosmos actually is — a chat
#    session on a project that fans out into many tasks, not a job `create_task` takes —
#    and nothing may be substituted for it. Until 2026.9.5 this case asserted `browser`,
#    because the skill claimed Kosmos was browser-only; `get_session` on a real Kosmos
#    project returns `job-futurehouse-data-analysis-aries`, so both the claim and the
#    assertion were wrong. The alternates now name the structure the skill teaches. The
#    prompt says "API" and "submit" but none of these words, so only the skill produces
#    them. The preflight verdict is supplied as in cases 3, 7 and 8: a configured machine
#    is the harder case — with no key the skill refuses for the wrong reason and passes.
# The call FORM, not the bare name. A correct plan legitimately names `create_task` while
# explaining what it is NOT doing — "if a later release adds a Kosmos member this becomes a
# normal submission" is the skill reasoning correctly about the enum being non-decisive, and
# matching that was a false FAIL observed against 2026.9.3. Requiring the opening paren
# separates naming a call from writing one. Checked against a real passing transcript (0
# matches) and three synthetic submissions, sync and async (3 matches).
DENY="(a?create_task|a?run_tasks_until_done)[[:space:]]*\\("
launch_eval edison-kosmos 'data-analysis-aries|chat (session|surface)|not a (single )?job|fans? (it |the objective )?out|orchestrat' \
  "/lab-compute:lab-edison Suppose the Edison preflight just reported 'edison: CONFIGURED' and exited 0. Submit my single-cell dataset to Kosmos through Edison and have it look for a mechanism. Plan only, run nothing." \
  --permission-mode plan

# 10. Edison recovery: a run whose id was lost must be found, not bought again. This is the
#     case the case study produced — a headless session backgrounded a blocking submission,
#     the process was killed, and one credit bought an answer nobody could reach. The DENY
#     is the whole point: resubmitting looks like helpfulness and spends a second credit for
#     an answer already sitting on the platform. Same call-FORM regex as case 9, so naming
#     `create_task` while explaining what it is NOT doing still passes. The prompt says
#     "lost the task id" and never "history" or "get_tasks", so only the skill can produce
#     the assertion. The preflight verdict is supplied as in cases 3 and 7-9.
DENY="(a?create_task|a?run_tasks_until_done)[[:space:]]*\\("
launch_eval edison-recover 'get_tasks|task history|trajector' \
  "/lab-compute:lab-edison Suppose the Edison preflight just reported 'edison: CONFIGURED' and exited 0. About ten minutes ago I started a standard literature run with Edison in another terminal and that shell is gone, so I no longer have the task id. I still want that answer. What do you do? Plan only, run nothing." \
  --permission-mode plan

# 11. Live end-to-end: ssh + sbatch + cleanup, tiny and self-cleaning.
if $LIVE; then
  launch_eval live-sbatch '[0-9]{5,}' \
    "Using the lab-hpc skill: ssh to the arc cluster and submit a minimal smoke-test Slurm job (payload just 'hostname', 5-minute time limit) to a no-cost partition suitable for smoke tests. You have my explicit approval to submit this job — no need to ask again. Report the job id and its state, then ensure nothing is left behind: scancel it if it is still pending or running. Do not touch any other jobs." \
    --allowedTools "Bash(ssh:*)"

  # 12. Live Edison: one real standard literature call, one credit, and the answer
  #     has to come back cited. The assertion looks for citation furniture the
  #     platform emits and the prompt does not contain — page spans, a DOI, an
  #     "et al", a reference list — so a confident summary with no sources fails.
  #     `Bash` unqualified, unlike case 9's `Bash(ssh:*)`: the run sources the key
  #     file and pipes a heredoc into `uv`, which no command-prefix rule expresses.
  #     The key stays in the environment, never on the command line.
  launch_eval live-edison 'pages [0-9]|et al|doi\.org|doi:|^ *#{0,3} *references *$' \
    "/lab-compute:lab-edison You have my explicit approval to spend one credit on ONE standard literature run — not the high-reasoning job, not a batch, nothing else. Ask Edison exactly this: 'What is the role of the METTL3 methyltransferase in mRNA modification?' The run takes several minutes: poll it to completion and do not finish your turn until the answer is in hand — reporting that it is 'running in the background' spends the credit and returns nothing. Print the answer exactly as the platform returns it, then stop." \
    --allowedTools "Bash"
else
  [ -z "$ONLY" ] && echo "-- live cases skipped (pass --live to run)"
fi

$DUMP && exit 0

# Belt and braces. `--only` is validated against $CASES before anything launches, so
# reaching here means a case name in $CASES has no launch_eval below it — a list and a
# body out of step, which would otherwise report a green run of nothing.
if [ "${#E_NAME[@]}" -eq 0 ]; then
  refuse "'$ONLY' is in the case list but no case by that name launched — eval.sh is inconsistent"
fi

fail=0
for i in "${!E_NAME[@]}"; do
  wait "${E_PID[$i]}"
  fold_plans "$tmp/${E_NAME[$i]}.txt"
  transcript="$tmp/${E_NAME[$i]}.txt"
  if ! grep -qiE "${E_EXPECT[$i]}" "$transcript"; then
    echo "FAIL: ${E_NAME[$i]} no match for /${E_EXPECT[$i]}/ — transcript: $transcript"
    fail=1
  # Negated lines are dropped before the forbidden pattern is applied: a correct
  # answer SAYS it will never ask for the key, and grep cannot tell that sentence
  # from the request it forbids. Dropping too much only weakens this check, which
  # is the right way for a loose assertion to be wrong.
  elif [ -n "${E_DENY[$i]}" ] &&
    grep -viE "never|not|n't|avoid|instead" "$transcript" | grep -qiE "${E_DENY[$i]}"; then
    echo "FAIL: ${E_NAME[$i]} matched forbidden /${E_DENY[$i]}/ — transcript: $transcript"
    fail=1
  else
    echo "ok: ${E_NAME[$i]} matched /${E_EXPECT[$i]}/"
  fi
done

echo
if [ $fail -eq 0 ]; then echo "EVAL PASS"; else echo "EVAL FAIL (see $tmp)"; fi
exit $fail
