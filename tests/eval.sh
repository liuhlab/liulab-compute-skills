#!/usr/bin/env bash
# Layer 3 — agent evals: run the skills through real headless Claude Code
# sessions and assert on the behavior they induce. COSTS TOKENS (one full
# claude -p session per case) and several minutes of wall time.
#
# Agents/automation: prefer a targeted `--only <case>` run; ASK the user
# before running the full suite or anything with --live (touches the real
# cluster). Cases run CONCURRENTLY, so a full run's wall time is roughly the
# slowest single case.
#
# NOTE: evals exercise the INSTALLED plugin (plugin cache), not this working
# tree — push + `claude plugin update lab-compute@liulab` first, or results
# reflect the previous version.
#
# Usage: eval.sh [--live] [--only <case>]
#   --live         also run the end-to-end case: the agent must ssh to arc
#                  and submit+clean up a tiny hostname job (real cluster).
#   --only <case>  run a single case
#                  (trigger|explicit|reject|containers|jupyter-ircbc|reuse-job|
#                   edison-refuse|live-sbatch)
#
# Assertions are loose key-phrase greps: evals are non-deterministic. On
# failure, read the saved transcript before concluding the skill is broken.
set -u
# `|| exit 1`: the cases below are written against the repo root, and a run that spends
# tokens from the wrong directory is worse than one that never starts.
cd "$(dirname "$0")/.." || exit 1
LIVE=false ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=true ;;
    --only) shift; ONLY="$1"; [ "$ONLY" = "live-sbatch" ] && LIVE=true ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lab-skill-eval.XXXXXX")
echo "transcripts: $tmp"

declare -a E_NAME E_EXPECT E_DENY E_PID

# Set DENY on the line before a launch_eval call to give that one case a second,
# NEGATIVE assertion: the transcript must not match this pattern. One regex cannot
# say "contains this and not that", and the Edison case needs both — a refusal that
# then asks for the key in chat is the failure the case exists to catch. The call
# consumes DENY, so it can never leak into the next case.
DENY=""

launch_eval() { # <name> <expected-regex> <prompt> [extra claude flags...]
  local name="$1" expect="$2" prompt="$3"; shift 3
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && { DENY=""; return 0; }
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

# 8. Live end-to-end: ssh + sbatch + cleanup, tiny and self-cleaning.
if $LIVE; then
  launch_eval live-sbatch '[0-9]{5,}' \
    "Using the lab-hpc skill: ssh to the arc cluster and submit a minimal smoke-test Slurm job (payload just 'hostname', 5-minute time limit) to a no-cost partition suitable for smoke tests. You have my explicit approval to submit this job — no need to ask again. Report the job id and its state, then ensure nothing is left behind: scancel it if it is still pending or running. Do not touch any other jobs." \
    --allowedTools "Bash(ssh:*)"
else
  [ -z "$ONLY" ] && echo "-- live-sbatch skipped (pass --live to run)"
fi

if [ "${#E_NAME[@]}" -eq 0 ]; then
  echo "no cases matched '--only $ONLY' (valid: trigger|explicit|reject|containers|jupyter-ircbc|reuse-job|edison-refuse|live-sbatch)"
  exit 2
fi

fail=0
for i in "${!E_NAME[@]}"; do
  wait "${E_PID[$i]}"
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
