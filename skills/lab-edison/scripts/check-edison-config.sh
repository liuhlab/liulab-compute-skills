#!/usr/bin/env bash
# Preflight: does THIS machine hold an Edison platform API key the client can read?
#
# One verdict line per condition, and on failure the exact remedy. It NEVER prints the key
# or any part of one — lengths and yes/no only, because whatever this writes lands in the
# agent's transcript. The remedy lives here, not in SKILL.md, so a verdict and its fix
# cannot drift apart and the agent relays tested text.
#
# An exported EDISON_PLATFORM_API_KEY wins; otherwise the key file, default
# ~/.claude/compute/edison.env. An interactive shell rc is invisible here — agent tool calls
# run non-interactive shells — which is why the file exists.
#
# Usage: check-edison-config.sh [-f <key_file>] [--constants]. `-f` reads that file INSTEAD
# of the default and ignores the environment variable — the gate drives this against
# fixtures, and on a maintainer's machine (where the real key IS exported) they would all
# report configured and prove nothing. Exit: 0 configured, 1 not.
#
# This file is the ONE owner of the four constants describing the key file: the variable
# name the client reads, the shipped placeholder, the file's location, and which permission
# modes are acceptable. `--constants` prints them and exits 0 without reading any key file,
# one `KEY=value` per line, so the gate can assert that the onboarding template, the
# published page and the no-secrets sweep still agree with these rather than each restating
# a literal. Nothing there is secret: the placeholder is the shipped value, and a real key
# is never read, let alone printed. `KEYFILE` reports the file this invocation would check,
# so `-f` moves it; call it without `-f` to read the shipped location.

set -u

VAR=EDISON_PLATFORM_API_KEY
PLACEHOLDER=PASTE-YOUR-EDISON-KEY-HERE
KEYFILE="$HOME/.claude/compute/edison.env"
# Owner-only is the rule; 600 is only the mode the remedy hands out. MODE_GLOB is what the
# test below actually applies, MODE_LABEL is the word prose should use for it, and
# CHMOD_MODE is what `chmod` is told. Saying "must be 600" anywhere is narrower than the
# check and made four documents disagree with this script.
MODE_GLOB='*00'
MODE_LABEL=owner-only
CHMOD_MODE=600
OVERRIDE=false
CONSTANTS=false

while [ $# -gt 0 ]; do
  case "$1" in
    -f) shift; [ $# -gt 0 ] || { echo "-f needs a file" >&2; exit 2; }
        KEYFILE="$1"; OVERRIDE=true ;;
    --constants) CONSTANTS=true ;;
    *)  echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

# $HOME collapsed to a tilde: an absolute home directory carries a username.
shown="$KEYFILE"
case "$KEYFILE" in "$HOME"/*) shown="~${KEYFILE#"$HOME"}" ;; esac

if $CONSTANTS; then
  echo "VAR=$VAR"
  echo "PLACEHOLDER=$PLACEHOLDER"
  echo "KEYFILE=$shown"
  echo "MODE_GLOB=$MODE_GLOB"
  echo "MODE_LABEL=$MODE_LABEL"
  echo "CHMOD_MODE=$CHMOD_MODE"
  exit 0
fi

# 1. The environment. Tested for emptiness, never printed.
envnote="$VAR is not exported here"
if $OVERRIDE; then envnote="the environment is ignored under -f"
elif [ -n "${EDISON_PLATFORM_API_KEY:-}" ]; then
  echo "key: SET (${#EDISON_PLATFORM_API_KEY} chars)"
  echo "edison: CONFIGURED (source: $VAR exported into this process)"
  exit 0
fi

# Printed on any failure. Nothing here is secret — the placeholder is the shipped value.
not_configured() { # <reason>
  echo "edison: NOT CONFIGURED ($1)"
  cat <<EOF

--- how to fix ---
mkdir -p ${shown%/*}
printf 'export ${VAR}=${PLACEHOLDER}\n' > ${shown}
chmod ${CHMOD_MODE} ${shown}

Then open ${shown} in your own editor and replace ${PLACEHOLDER} with the key from the
Edison platform. Never paste a key into a chat, a command line, or a job script.

${VAR} is the only name edison-client reads; the vendor's README names a different one and
is wrong. A key exported from ~/.zshrc is usually invisible to this check, because tool
calls run non-interactive shells that never read an interactive rc — the file fixes that.
EOF
  exit 1
}

# 2. The key file, condition by condition.
[ -f "$KEYFILE" ] || { echo "key file: MISSING ($shown)"; not_configured "no key file, and $envnote"; }
echo "key file: PRESENT ($shown)"
[ -s "$KEYFILE" ] || { echo "key file: EMPTY (0 bytes)"; not_configured "key file is empty"; }
echo "key file: NON-EMPTY ($(wc -c <"$KEYFILE" | tr -d ' ') bytes)"

# The assignment, taken by name. `${VAR}` rather than the name spelled out, so this line is
# not itself an assignment for the no-secrets sweep to flag. Last one wins, as when sourced.
value=$(sed -n "s/^[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}${VAR}[[:space:]]*=[[:space:]]*//p" \
  "$KEYFILE" | tail -n 1)
# Strip one layer of matching quotes, as sourcing the file would.
for q in '"' "'"; do value=${value%"$q"}; value=${value#"$q"}; done

reason=""
if [ -z "$value" ]; then
  echo "key: NOT SET (the file assigns no $VAR — the exact name edison-client reads)"
  reason="the key file assigns no $VAR"
elif [ "$value" = "$PLACEHOLDER" ]; then
  echo "key: PLACEHOLDER (still the shipped value)"; reason="the placeholder was never replaced"
else
  echo "key: SET (${#value} chars)"
fi

# MODE_GLOB means group and other bits are zero, so 600 and 400 both pass. `stat -c` first:
# GNU accepts it and BSD rejects it, whereas BSD's `-f` reads a FILESYSTEM under GNU.
mode=$(stat -c '%a' "$KEYFILE" 2>/dev/null || stat -f '%Lp' "$KEYFILE" 2>/dev/null || echo "?")
label=$(printf '%s' "$MODE_LABEL" | tr '[:lower:]' '[:upper:]')
# Unquoted on purpose: the glob has to glob. shellcheck reads it as a word-splitting risk.
# shellcheck disable=SC2254
case "$mode" in
  $MODE_GLOB) echo "key file: PERMISSIONS $label (mode $mode)" ;;
  *)   echo "key file: PERMISSIONS TOO OPEN (mode $mode — run: chmod $CHMOD_MODE $shown)"
       reason="${reason:+$reason; }mode $mode lets other people read it" ;;
esac

[ -z "$reason" ] || not_configured "$reason"
echo "edison: CONFIGURED (source: key file $shown)"
