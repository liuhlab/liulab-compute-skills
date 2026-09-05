#!/usr/bin/env bash
# Layer 2 — environment preflight: is THIS machine set up for lab compute? It runs the very
# checks the skills run as their own step 0, so a green preflight and a skill that then
# refuses cannot disagree.
#
# Three checks, and only one of them gates the exit code. The cluster check is the lab's
# baseline, so it decides. The two Edison checks are reported and never decide: a platform key
# is per-user and opt-in, and a machine without one is correctly configured for everything
# else. Failing on it would teach people to ignore this script.
#
# Nothing here reads a key. The preflight reports lengths and verdicts, and this file adds
# only what is true of the machine around it.
#
# Usage: preflight.sh [--live]   (--live also opens a connection to each login node)
set -u
here=$(dirname "$0")
root=$(cd "$here/.." && pwd)

echo "== clusters =="
bash "$here/../skills/lab-hpc/scripts/check-hpc-config.sh" "$@"
rc=$?

# No "$@": --live means "reach the login nodes", which the Edison check has no notion of and
# would reject as an unknown argument. A bare interpreter and a path, because this check must
# work before anything is installed — the same reason `tests/lint.sh` invokes it that way.
echo
echo "== edison key (optional) =="
python3 "$root/src/edison_cli/preflight.py" ||
  echo "(Edison is opt-in per user — this does not fail the preflight.)"

# The key is only half of it. The spend path is a Python package now, so `edison-cli` also
# needs pixi and a built environment. This REPORTS; it never builds one, because a report that
# spends twenty seconds and 600 MB is a report nobody runs twice.
echo
echo "== edison-cli environment (optional) =="
if ! command -v pixi >/dev/null 2>&1; then
  echo "pixi: MISSING — edison-cli runs inside a pixi environment, so pixi comes first"
  echo "(every other skill here is bash and is unaffected.)"
else
  echo "pixi: PRESENT ($(pixi --version 2>/dev/null))"
  prefix=$(pixi info --manifest-path "$root/pyproject.toml" --json 2>/dev/null |
    python3 -c 'import json,sys
try:
    info = json.load(sys.stdin)
except ValueError:
    raise SystemExit(0)
for env in info.get("environments_info", []):
    if env.get("name") == "default":
        print(env.get("prefix") or "")
        break' 2>/dev/null)
  if [ -z "$prefix" ]; then
    echo "manifest: UNREADABLE — pixi could not read $root/pyproject.toml"
  elif [ -x "$prefix/bin/edison-cli" ]; then
    echo "edison-cli: BUILT and on the environment's path"
  else
    echo "edison-cli: NOT BUILT YET — the first Edison command builds it (about 20 s, once)"
    echo "  pixi run --manifest-path <plugin-root>/pyproject.toml edison-cli preflight"
  fi
fi

exit "$rc"
