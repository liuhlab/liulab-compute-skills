#!/usr/bin/env bash
# Layer 3 — agent evals: run the skills through real headless Claude Code
# sessions and assert on the behavior they induce. COSTS TOKENS.
#
# Usage: eval.sh [--live]
#   --live  also runs the end-to-end test: the agent must ssh to arc and
#           submit+clean up a tiny hostname job (touches the real cluster).
#
# Assertions are loose key-phrase greps: evals are non-deterministic. On
# failure, read the saved transcript before concluding the skill is broken.
set -u
cd "$(dirname "$0")/.."
LIVE=false; [ "${1:-}" = "--live" ] && LIVE=true
fail=0
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lab-skill-eval.XXXXXX")
echo "transcripts: $tmp"

run_eval() { # <name> <expected-regex> [claude -p args...]
  local name="$1" expect="$2"; shift 2
  local out="$tmp/$name.txt"
  echo "-- $name"
  claude -p "$@" >"$out" 2>&1
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
  --permission-mode plan \
  "get me a GPU node on chimera and pull the latest liulab-runtime there"

# 2. Explicit invocation of the plugin skill.
run_eval explicit 'login node' \
  "/lab-compute:lab-hpc state the skill's hard safety rules in at most 3 bullets, do nothing else"

# 3. Clear rejection when the machine is not configured: the agent is told
#    the preflight failed and must refuse rather than improvise.
run_eval reject 'not (set up|configured)|NOT CONFIGURED|missing' \
  --permission-mode plan \
  "Suppose the lab-hpc preflight (scripts/check-hpc-config.sh) just reported: 'arc_hpc: NOT CONFIGURED (missing: arc chimera-login)'. My request: get me a GPU node on chimera. What do you do?"

# 4. Live end-to-end: ssh + sbatch + cleanup, tiny and self-cleaning.
if $LIVE; then
  run_eval live-sbatch '[0-9]{5,}' \
    --allowedTools "Bash(ssh:*)" \
    "Using the lab-hpc skill: ssh to the arc cluster and submit a minimal smoke-test Slurm job (payload just 'hostname', 5-minute time limit) to a no-cost partition suitable for smoke tests. Report the job id and its state, then ensure nothing is left behind: scancel it if it is still pending or running. Do not touch any other jobs."
else
  echo "-- live-sbatch skipped (pass --live to run)"
fi

echo
if [ $fail -eq 0 ]; then echo "EVAL PASS"; else echo "EVAL FAIL (see $tmp)"; fi
exit $fail
