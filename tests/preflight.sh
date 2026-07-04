#!/usr/bin/env bash
# Layer 2 — environment preflight: is THIS machine configured for the lab
# clusters? Delegates to the exact check the lab-hpc skill runs as step 0.
# Usage: preflight.sh [--live]
exec bash "$(dirname "$0")/../skills/lab-hpc/scripts/check-hpc-config.sh" "$@"
