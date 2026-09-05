#!/usr/bin/env bash
# Layer 1 — static lint. No network, no model. Run on every change.
set -u
# `|| exit 1`, because every check below is relative to the repo root. A failed cd would
# otherwise leave the sweep running somewhere else, finding no secrets because it is
# looking at nothing, and reporting LINT PASS. A gate that cannot reach the tree it
# guards must fail, not pass.
cd "$(dirname "$0")/.." || exit 1
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
# 1536 is `skillListingMaxDescChars`: the platform's cap on ONE description in the skill
# listing. It is enforced per skill, below.
DESC_MAX=1536
total_desc=0
n_skills=0
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
  if [ "${dlen:-0}" -lt 20 ]; then err "$s description missing or too short"
  elif [ "$dlen" -gt "$DESC_MAX" ]; then
    err "$s description ${dlen} chars exceeds the ${DESC_MAX}-char per-skill listing cap"
  else ok "$s description present (${dlen}/${DESC_MAX} chars)"; fi
  total_desc=$((total_desc + dlen))
  n_skills=$((n_skills + 1))
done
# The sum is INFORMATION. It carried a FAIL until 2026-09, on the reading that 1536 was a
# budget the skills shared. It is not: it caps a single description, which is why the check
# above is per skill. The budget that really is shared is a fraction of the model's context
# window, and it spans every skill installed on the machine — other plugins, the user's own
# — not this plugin's. No number here can measure that, so nothing here may fail on it, and
# adding a skill must not fail the gate. Do not reinstate the sum.
ok "descriptions total ${total_desc} chars across ${n_skills} skills (informational)"

echo "== no-secrets sweep =="
# Publishable tree only (what git tracks + working copies), minus this test
# and the gitignored build and cache trees. Nothing excluded here is publishable
# — every entry is in .gitignore, and this list is kept in step with it.
# `.pixi/` holds vendored conda packages carrying both IP literals and key
# material, and `.ruff_cache/` stores absolute paths (so, the local username):
# sweeping either would turn this gate permanently red the day someone runs
# `pixi run check`, which is the fastest way to get the gate disabled.
# `--exclude=.git` is NOT redundant with `--exclude-dir=.git`: in a linked git
# worktree `.git` is a FILE holding `gitdir: <absolute path>`, which contains the
# local username — so without it this gate flags its own plumbing and reports a
# leak that is not there. A false positive here is how a security gate gets
# switched off, so both spellings stay.
SWEEP() { grep -rnE "$1" \
  --exclude-dir=.git --exclude=.git --exclude-dir=.claude --exclude-dir=.pixi \
  --exclude-dir=site --exclude-dir=dist --exclude-dir=build \
  --exclude-dir=.cache --exclude-dir=__pycache__ \
  --exclude-dir=.ruff_cache --exclude-dir=.mypy_cache \
  --exclude-dir=.pytest_cache \
  --exclude=lint.sh . ; }
# 0.0.0.0 / 127.0.0.1 are well-known non-secret addresses (used in the
# "bind to localhost only" safety instructions) — everything else flags.
if SWEEP '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -vE '0\.0\.0\.0|127\.0\.0\.1'; then
  err "IPv4-looking literal found (above)"
else ok "no IP literals (0.0.0.0/127.0.0.1 exempt)"; fi
if SWEEP 'Identity[F]ile|BEGIN [A-Z ]*PRIVATE[ ]KEY|ssh-(rsa|ed25519)[ ]AAAA'; then
  err "key material / IdentityFile reference found (above)"
else ok "no key material"; fi
# Usernames come from THIS machine's ssh config at test time — none are
# stored in the repo, but none may appear in it either. Shared CI service
# accounts are exempt for the same reason the hostname sweep below exempts
# the public forges: every GitHub-hosted machine runs as the same well-known
# name, which is nobody's identity and is also an ordinary English word this
# repo's own prose (and the copied scripts/check.sh) uses. It can never be a
# lab username, so exempting it costs the sweep nothing.
users=$( (awk 'tolower($1)=="user"{print $2}' ~/.ssh/config 2>/dev/null; whoami) \
         | grep -vxE 'runner' | sort -u)
uleak=0
for u in $users; do
  if SWEEP "(^|[^a-zA-Z0-9_-])$u([^a-zA-Z0-9_-]|\$)"; then
    err "local username '$u' appears in the repo (above)"
    uleak=1
  fi
done
# Guarded, because an unconditional success line printed `ok: no usernames leaked`
# directly beneath `FAIL: username appears in the repo`. A gate that contradicts
# itself in the same breath teaches the reader to skim past both.
if [ "$uleak" -eq 0 ]; then
  ok "no local ssh-config usernames leaked (checked $(printf '%s\n' "$users" | grep -c .) names)"
fi
# Hostnames likewise come from THIS machine's ssh config at test time — the
# repo may reference hosts only by alias. Only dotted values are swept
# (single-label names are indistinguishable from alias vocabulary); wildcards
# and public forges are skipped; IP-valued HostNames also trip the IP sweep.
hosts=$(awk 'tolower($1)=="hostname"{print $2}' ~/.ssh/config 2>/dev/null \
        | grep '\.' | grep -v '[*?%]' \
        | grep -viE '^(localhost|127\.0\.0\.1|github\.com|gitlab\.com|bitbucket\.org)$' \
        | sort -u)
hcount=0
hleak=0
for h in $hosts; do
  hcount=$((hcount + 1))
  hre=$(printf '%s' "$h" | sed 's/[][\.^$*+?(){}|]/\\&/g')
  if SWEEP "(^|[^a-zA-Z0-9._-])$hre([^a-zA-Z0-9._-]|\$)"; then
    err "local ssh-config hostname '$h' appears in the repo (above)"
    hleak=1
  fi
done
if [ "$hleak" -eq 0 ]; then
  ok "no local ssh-config hostnames leaked (checked $hcount names)"
fi

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
