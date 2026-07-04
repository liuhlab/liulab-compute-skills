#!/usr/bin/env bash
# Layer 1 — static lint. No network, no model. Run on every change.
set -u
cd "$(dirname "$0")/.."
fail=0
err() { echo "FAIL: $*"; fail=1; }
ok()  { echo "  ok: $*"; }

echo "== manifests =="
for f in .claude-plugin/marketplace.json .claude-plugin/plugin.json; do
  if python3 -m json.tool "$f" >/dev/null 2>&1; then ok "$f is valid JSON"
  else err "$f is not valid JSON"; fi
done

plug=$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["name"])' 2>/dev/null)
case "$plug" in
  lab-*) ok "plugin name '$plug' follows lab-* policy" ;;
  *)     err "plugin name '$plug' must be lab-* (not liulab-*)" ;;
esac

echo "== skills =="
total_desc=0
for d in skills/*/; do
  s="${d}SKILL.md"
  name=$(basename "$d")
  [ -f "$s" ] || { err "$d has no SKILL.md"; continue; }
  fm_name=$(awk 'f && $1=="name:"{print $2; exit} /^---$/{f++}' "$s")
  if [ "$fm_name" = "$name" ]; then ok "$s frontmatter name matches dir"
  else err "$s frontmatter name '$fm_name' != dir '$name'"; fi
  case "$name" in
    lab-*) ok "skill '$name' follows lab-* policy" ;;
    *)     err "skill '$name' must be lab-* (not liulab-*)" ;;
  esac
  dlen=$(python3 - "$s" <<'EOF'
import sys
lines = open(sys.argv[1]).read().splitlines()
assert lines[0] == "---", "no frontmatter"
body, in_desc = [], False
for ln in lines[1:]:
    if ln == "---": break
    if ln.startswith("description:"):
        in_desc = True
        body.append(ln.split(":", 1)[1].strip().lstrip(">-").strip())
    elif in_desc and (ln.startswith("  ") or not ln.strip()):
        body.append(ln.strip())
    else:
        in_desc = False
print(len(" ".join(w for w in body if w)))
EOF
  ) || { err "$s frontmatter unparseable"; continue; }
  if [ "${dlen:-0}" -ge 20 ]; then ok "$s description present (${dlen} chars)"
  else err "$s description missing or too short"; fi
  total_desc=$((total_desc + dlen))
done
if [ "$total_desc" -le 1536 ]; then ok "combined description budget ${total_desc}/1536 chars"
else err "combined descriptions ${total_desc} chars exceed the 1536-char listing budget"; fi

echo "== no-secrets sweep =="
# Publishable tree only (what git tracks + working copies), minus this test.
SWEEP() { grep -rnE "$1" --exclude-dir=.git --exclude-dir=.claude --exclude=lint.sh . ; }
if SWEEP '([0-9]{1,3}\.){3}[0-9]{1,3}'; then
  err "IPv4-looking literal found (above)"
else ok "no IP literals"; fi
if SWEEP 'Identity[F]ile|BEGIN [A-Z ]*PRIVATE[ ]KEY|ssh-(rsa|ed25519)[ ]AAAA'; then
  err "key material / IdentityFile reference found (above)"
else ok "no key material"; fi
# Usernames come from THIS machine's ssh config at test time — none are
# stored in the repo, but none may appear in it either.
users=$( (awk 'tolower($1)=="user"{print $2}' ~/.ssh/config 2>/dev/null; whoami) | sort -u)
for u in $users; do
  if SWEEP "(^|[^a-zA-Z0-9_-])$u([^a-zA-Z0-9_-]|\$)"; then
    err "local username '$u' appears in the repo (above)"
  fi
done
ok "no local ssh-config usernames leaked (checked $(echo "$users" | wc -l | tr -d ' ') names)"

echo "== check-hpc-config.sh self-test =="
out=$(bash skills/lab-hpc/scripts/check-hpc-config.sh -F /dev/null)
rc=$?
if [ $rc -eq 1 ] && ! printf '%s' "$out" | grep -v 'NOT CONFIGURED' | grep -q CONFIGURED; then
  ok "empty ssh config → both clusters NOT CONFIGURED, exit 1"
else
  err "check-hpc-config.sh with empty config: expected NOT CONFIGURED + exit 1, got exit $rc: $out"
fi

echo
if [ $fail -eq 0 ]; then echo "LINT PASS"; else echo "LINT FAIL"; fi
exit $fail
