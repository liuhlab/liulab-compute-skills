#!/usr/bin/env bash
# Layer 2 — environment preflight: is THIS machine set up for lab compute? It runs the very
# checks the skills run as their own step 0, so a green preflight and a skill that then
# refuses cannot disagree.
#
# Two checks, and only one of them gates the exit code. The cluster check is the lab's
# baseline, so it decides. The Edison check is reported and never decides: a platform key is
# per-user and opt-in, and a machine without one is correctly configured for everything else.
# Failing on it would teach people to ignore this script.
#
# Usage: preflight.sh [--live]   (--live also opens a connection to each login node)
set -u
here=$(dirname "$0")

echo "== clusters =="
bash "$here/../skills/lab-hpc/scripts/check-hpc-config.sh" "$@"
rc=$?

# No "$@": --live means "reach the login nodes", which the Edison check has no notion of and
# would reject as an unknown argument.
echo
echo "== edison (optional) =="
bash "$here/../skills/lab-edison/scripts/check-edison-config.sh" ||
  echo "(Edison is opt-in per user — this does not fail the preflight.)"

exit "$rc"
