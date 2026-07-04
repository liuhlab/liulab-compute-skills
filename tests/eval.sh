#!/usr/bin/env bash
# Layer 3 — agent evals: run the skills through real headless Claude Code
# sessions and assert on the behavior they induce. COSTS TOKENS.
#
# Usage: eval.sh [--live] [--only <case>]
#   --live         also run the end-to-end case: the agent must ssh to arc
#                  and submit+clean up a tiny hostname job (real cluster).
#   --only <case>  run a single case
#                  (trigger|explicit|reject|containers|live-sbatch)
#
# Assertions are loose key-phrase greps: evals are non-deterministic. On
# failure, read the saved transcript before concluding the skill is broken.
set -u
cd "$(dirname "$0")/.."
LIVE=false ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=true ;;
    --only) shift; ONLY="$1"; [ "$ONLY" = "live-sbatch" ] && LIVE=true ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done
fail=0
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lab-skill-eval.XXXXXX")
echo "transcripts: $tmp"

run_eval() { # <name> <expected-regex> <prompt> [extra claude flags...]
  local name="$1" expect="$2" prompt="$3"; shift 3
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && return 0
  local out="$tmp/$name.txt"
  echo "-- $name"
  # NOTE: prompt must precede flags — variadic flags (--allowedTools) would
  # otherwise swallow it.
  claude -p "$prompt" "$@" >"$out" 2>&1
  if grep -qiE "$expect" "$out"; then
    echo "  ok: matched /$expect/"
  else
    echo "  FAIL: no match for /$expect/ — transcript: $out"
    fail=1
  fi
}

# 1. Auto-trigger: HPC-flavored prompt, skill never named, plan mode (no
#    execution). Expect a Slurm-first plan, not naive ssh-and-run.
run_eval trigger 'slurm|sbatch|salloc|squeue|compute node' \
  "get me a GPU node on chimera and pull the latest liulab-runtime there" \
  --permission-mode plan

# 2. Explicit invocation of the plugin skill.
run_eval explicit 'login node' \
  "/lab-compute:lab-hpc state the skill's hard safety rules in at most 3 bullets, do nothing else"

# 3. Clear rejection when the machine is not configured: the agent is told
#    the preflight failed and must refuse rather than improvise.
run_eval reject 'not (set up|configured)|NOT CONFIGURED|missing' \
  "Suppose the lab-hpc preflight (scripts/check-hpc-config.sh) just reported: 'arc_hpc: NOT CONFIGURED (missing: arc chimera-login)'. My request: get me a GPU node on chimera. What do you do?" \
  --permission-mode plan

# 4. Recipe skill triggers: image build request must surface the
#    lab-containers pull-on-login / build-in-compute-job procedure.
run_eval containers 'crane|docker-archive|login node|sbatch' \
  "rebuild the align-rna singularity image on ircbc" \
  --permission-mode plan

# 5. Live end-to-end: ssh + sbatch + cleanup, tiny and self-cleaning.
if $LIVE; then
  run_eval live-sbatch '[0-9]{5,}' \
    "Using the lab-hpc skill: ssh to the arc cluster and submit a minimal smoke-test Slurm job (payload just 'hostname', 5-minute time limit) to a no-cost partition suitable for smoke tests. You have my explicit approval to submit this job — no need to ask again. Report the job id and its state, then ensure nothing is left behind: scancel it if it is still pending or running. Do not touch any other jobs." \
    --allowedTools "Bash(ssh:*)"
else
  echo "-- live-sbatch skipped (pass --live to run)"
fi

echo
if [ $fail -eq 0 ]; then echo "EVAL PASS"; else echo "EVAL FAIL (see $tmp)"; fi
exit $fail
