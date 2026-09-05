#!/usr/bin/env bash
# Preflight: does THIS machine hold an Edison platform API key the client can read?
#
# Prints one verdict line per condition. It NEVER prints the key, or any prefix
# or suffix of one — lengths and yes/no only, because whatever this script writes
# lands in the agent's transcript.
#
# Resolution order, and the order matters:
#   1. EDISON_PLATFORM_API_KEY already exported into this process — configured.
#   2. otherwise the key file, default ~/.claude/compute/edison.env.
# An interactive shell rc is invisible here: agent tool calls run non-interactive
# shells, which never read ~/.zshrc or ~/.bashrc, so a key the user can see in
# their own terminal is routinely absent from this process. The dedicated file at
# mode 600 is the documented home for exactly that reason.
#
# Usage: check-edison-config.sh [-f <key_file>]
#   -f file  read this file INSTEAD of the default, and ignore the environment
#            variable entirely. Suppressing the environment is half of what the
#            flag is for: the gate drives this script against fixtures, and on a
#            maintainer's machine — the one machine where the real key IS
#            exported — every fixture would otherwise report configured and the
#            gate would pass having tested nothing.
#
# Exit: 0 configured, 1 not.

set -u

VAR=EDISON_PLATFORM_API_KEY
PLACEHOLDER=PASTE-YOUR-EDISON-KEY-HERE
KEYFILE="$HOME/.claude/compute/edison.env"
OVERRIDE=false

while [ $# -gt 0 ]; do
  case "$1" in
    -f)
      shift
      [ $# -gt 0 ] || { echo "-f needs a file" >&2; exit 2; }
      KEYFILE="$1"; OVERRIDE=true
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

# Paths are printed with $HOME collapsed back to a tilde: the verdict lines are
# read out in a transcript, and an absolute home directory carries a username.
tilde='~'
shown="$KEYFILE"
case "$KEYFILE" in
  "$HOME"/*) shown="$tilde${KEYFILE#"$HOME"}" ;;
esac

# 1. The environment. Tested for emptiness, never printed.
if $OVERRIDE; then
  envnote="the environment is ignored under -f"
else
  envnote="$VAR is not exported here"
  if [ -n "${EDISON_PLATFORM_API_KEY:-}" ]; then
    echo "key: SET (${#EDISON_PLATFORM_API_KEY} chars)"
    echo "edison: CONFIGURED (source: $VAR exported into this process)"
    exit 0
  fi
fi

# 2. The key file, condition by condition.
if [ ! -f "$KEYFILE" ]; then
  echo "key file: MISSING ($shown)"
  echo "edison: NOT CONFIGURED (no key file, and $envnote)"
  exit 1
fi
echo "key file: PRESENT ($shown)"

if [ ! -s "$KEYFILE" ]; then
  echo "key file: EMPTY (0 bytes)"
  echo "edison: NOT CONFIGURED (key file is empty)"
  exit 1
fi
echo "key file: NON-EMPTY ($(wc -c <"$KEYFILE" | tr -d ' ') bytes)"

# The assignment, taken by name. `${VAR}` rather than the name spelled out, so
# this line is not itself an assignment of the key variable for the no-secrets
# sweep to flag. The last assignment wins, as it would when sourced.
value=$(sed -n "s/^[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}${VAR}[[:space:]]*=[[:space:]]*//p" \
  "$KEYFILE" | tail -n 1)
value=${value%\"}; value=${value#\"}
value=${value%\'}; value=${value#\'}

ok=0
if [ -z "$value" ]; then
  echo "key: NOT SET (the file assigns no $VAR — that exact name is what edison-client reads)"
  ok=1
elif [ "$value" = "$PLACEHOLDER" ]; then
  echo "key: PLACEHOLDER (still the shipped value — paste your own key into $shown)"
  ok=1
else
  echo "key: SET (${#value} chars)"
fi

# Owner-only means group and other bits are both zero, so 600 and 400 both pass.
# `stat -c` first: GNU accepts it, BSD rejects the option outright, whereas BSD's
# `-f` reads a FILESYSTEM under GNU and would answer for the wrong thing.
mode=$(stat -c '%a' "$KEYFILE" 2>/dev/null || stat -f '%Lp' "$KEYFILE" 2>/dev/null || echo "?")
case "$mode" in
  *00) echo "key file: PERMISSIONS OWNER-ONLY (mode $mode)" ;;
  *)
    echo "key file: PERMISSIONS TOO OPEN (mode $mode — run: chmod 600 $shown)"
    ok=1
    ;;
esac

if [ "$ok" -eq 0 ]; then
  echo "edison: CONFIGURED (source: key file $shown)"
else
  echo "edison: NOT CONFIGURED (see the verdicts above)"
fi
exit "$ok"
