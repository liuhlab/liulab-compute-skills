#!/usr/bin/env bash
# Preflight: is THIS machine configured for the lab HPC clusters?
#
# Checks that the lab's conventional ssh aliases resolve via the user's own
# ssh config (`ssh -G`; honors Include). Contains no hostnames, usernames,
# or keys — it only verifies that the user has configured their own.
#
# Usage: check-hpc-config.sh [--live] [-F <ssh_config>]
#   --live   additionally try a BatchMode connection to each login alias
#   -F file  use an alternate ssh config (for testing this script)
#
# Output: one line per cluster: "<cluster>: CONFIGURED" or
#         "<cluster>: NOT CONFIGURED (missing: ...)" (+ live results).
# Exit:   0 if at least one cluster is fully configured, 1 otherwise.

set -u

LIVE=false
SSHCFG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=true ;;
    -F) shift; SSHCFG="$1" ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

sshg() { # ssh wrapper honoring the optional -F override (bash-3.2 safe)
  if [ -n "$SSHCFG" ]; then ssh -F "$SSHCFG" "$@"; else ssh "$@"; fi
}

# An alias counts as configured when the user's ssh config actually defines
# it: resolved hostname differs from the alias, or a proxyjump/remotecommand
# is attached (compute-node aliases keep hostname == alias via ProxyJump).
alias_configured() {
  local a="$1" out host pj rc
  out=$(sshg -G "$a" 2>/dev/null) || return 1
  host=$(printf '%s\n' "$out" | awk '$1=="hostname"{print $2; exit}')
  pj=$(printf '%s\n' "$out" | awk '$1=="proxyjump"{print $2; exit}')
  rc=$(printf '%s\n' "$out" | awk '$1=="remotecommand"{print $2; exit}')
  [ "$host" != "$a" ] || [ -n "$pj" ] || [ -n "$rc" ]
}

check_cluster() {
  local name="$1" login="$2"; shift 2
  local missing=()
  local a
  for a in "$@"; do
    alias_configured "$a" || missing+=("$a")
  done
  if [ ${#missing[@]} -eq 0 ]; then
    echo "$name: CONFIGURED"
    if $LIVE; then
      if sshg -o BatchMode=yes -o ConnectTimeout=8 "$login" true 2>/dev/null; then
        echo "$name: LIVE OK ($login reachable)"
      else
        if [ "$name" = "ircbc_hpc" ]; then
          echo "$name: LIVE FAIL ($login unreachable — VPN likely down; stop and tell the user)"
        else
          echo "$name: LIVE FAIL ($login unreachable)"
        fi
      fi
    fi
    return 0
  else
    echo "$name: NOT CONFIGURED (missing: ${missing[*]})"
    return 1
  fi
}

ok=1
check_cluster arc_hpc arc \
  arc chimera-login chimera-transfer chimera-gpu chimera-cpu && ok=0
check_cluster ircbc_hpc ircbc \
  ircbc ircbc-transfer cpu01 cpu02 cpu03 cpu04 cpu05 cpu06 cpu07 cpu08 && ok=0

exit $ok
