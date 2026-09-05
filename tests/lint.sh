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
# The Edison platform API key. Only the shipped placeholder may stand on the
# right of an assignment. Both spellings are swept: `EDISON_PLATFORM_API_KEY` is
# the name `edison-client` actually reads, and `EDISON_KEY` is the near miss a
# user who set it up from memory would write — a real key committed under the
# wrong name is exactly as leaked as one committed under the right name.
if SWEEP '(EDISON_PLATFORM_API_KEY|EDISON_KEY)[[:space:]]*=' | grep -v 'PASTE-YOUR-EDISON-KEY-HERE'; then
  err "Edison API key assigned to something other than the placeholder (above)"
else ok "no Edison API key (only the PASTE-YOUR-... placeholder)"; fi
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

echo "== vendor attribution =="
# The Edison platform is run by Edison Scientific, FutureHouse's commercial spinout, and the
# Edison entry in CONTEXT.md is the single authority on that. Four other registers say it in
# their own words — the skill body, its trigger description, README.md and the published page
# — and nothing can lint five registers for "says the right thing". This lints all of them
# for "never says the wrong thing". Same shape as the eval suite's DENY assertions, which
# guard one specific wrong job value the same way.
#
# Three appearances of the old name are CORRECT and must survive:
#   * the platform's job-name strings, `job-futurehouse-...`;
#   * the persona picker's handle, `@FutureHouse/...`;
#   * CHANGELOG.md, whose entries record what shipped and are not rewritten afterwards.
# The first two are naming residue of the spinout and are live API values — eliding them here
# is what stops this rule being "fixed" by editing a string the client has to send verbatim.
#
# Narrow on purpose: a regression test for one known error, not a factual-claims checker. It
# matches the shapes that put FutureHouse in charge of the platform and nothing else, so
# "Edison Scientific, FutureHouse's commercial spinout" passes and must keep passing.
VENDOR_WRONG='future[ -]?house[^[:space:]]{0,2}[[:space:]]+'
VENDOR_WRONG="$VENDOR_WRONG"'(edison|research|platform|product|service|api|client'
VENDOR_WRONG="$VENDOR_WRONG"'|runs?|operates?|owns?|hosts?|provides?)'
VENDOR_WRONG="$VENDOR_WRONG"'|(run|built|operated|owned|made|developed|provided|hosted|created)'
VENDOR_WRONG="$VENDOR_WRONG"'[[:space:]]+by[[:space:]]+future[ -]?house'
vendor_elide() { sed -e 's/job-futurehouse-[A-Za-z0-9._-]*//g' -e 's|@FutureHouse/[A-Za-z0-9._-]*||g'; }

# Both directions, every run. A sweep that can no longer fire looks exactly like a sweep that
# passes, and this one guards prose that nothing else re-checks.
vendor_probe() { # <label> <trips|clears> <text>
  local label="$1" want="$2" text="$3" got
  if printf '%s\n' "$text" | vendor_elide | grep -qiE "$VENDOR_WRONG"; then got=trips; else got=clears; fi
  if [ "$got" = "$want" ]; then ok "vendor probe: $label $want the check"
  else err "vendor probe: $label — wanted '$want', got '$got': $text"; fi
}
vendor_probe "the possessive re-attribution" trips  "FutureHouse's Edison research platform, reached from a lab machine"
vendor_probe "the bare adjective form"       trips  "the FutureHouse Edison platform"
vendor_probe "the run-by form"               trips  "the Edison platform, run by FutureHouse"
vendor_probe "the corrected attribution"     clears "run by Edison Scientific — FutureHouse's commercial spinout"
vendor_probe "a job-name string"             clears "get_session returns job-futurehouse-data-analysis-aries"
vendor_probe "the persona picker handle"     clears "the picker offers @FutureHouse/data-analysis-aries"

# CHANGELOG.md is excluded by name rather than by pattern: its older entries carry the wrong
# attribution as shipped history, and rewriting a release note to satisfy a linter hides the
# error instead of correcting it.
vendor_hits=$(SWEEP '[Ff]uture[ -]?[Hh]ouse' | grep -v '^\./CHANGELOG\.md:' \
              | vendor_elide | grep -iE "$VENDOR_WRONG")
if [ -n "$vendor_hits" ]; then
  printf '%s\n' "$vendor_hits"
  err "the Edison platform is attributed to FutureHouse (above, with job names elided) — Edison Scientific runs it; CONTEXT.md's Edison entry is the authority"
else
  ok "no FutureHouse attribution of the Edison platform (CHANGELOG history exempt)"
fi

echo "== check-hpc-config.sh self-test =="
out=$(bash skills/lab-hpc/scripts/check-hpc-config.sh -F /dev/null)
rc=$?
if [ $rc -eq 1 ] && ! printf '%s' "$out" | grep -v 'NOT CONFIGURED' | grep -q CONFIGURED; then
  ok "empty ssh config → both clusters NOT CONFIGURED, exit 1"
else
  err "check-hpc-config.sh with empty config: expected NOT CONFIGURED + exit 1, got exit $rc: $out"
fi

echo "== check-edison-config.sh self-test =="
# Fixtures are built here and deleted on the way out; none is ever committed.
# A committed fixture holding a fake key would trip the Edison rule in the sweep
# above — which is the rule working, not a false positive, so the fixtures live
# outside the tree the sweep reads.
# Every case passes `-f`, which also suppresses the environment variable: on a
# maintainer's machine the real key IS exported, and without that suppression
# all three fixtures would report configured and prove nothing.
edison_pf=skills/lab-edison/scripts/check-edison-config.sh
fx=$(mktemp -d "${TMPDIR:-/tmp}/lab-edison-fixtures.XXXXXX")
trap 'rm -rf "$fx"' EXIT

edison_case() { # <label> <key-file> <expected-verdict-substring> <expected-exit>
  local label="$1" file="$2" want="$3" wantrc="$4" out rc
  out=$(bash "$edison_pf" -f "$file")
  rc=$?
  if [ "$rc" -eq "$wantrc" ] && printf '%s\n' "$out" | grep -qF "$want"; then
    ok "edison preflight: $label"
  else
    err "edison preflight: $label — wanted '$want' and exit $wantrc, got exit $rc: $out"
  fi
}

printf 'export EDISON_PLATFORM_API_KEY=PASTE-YOUR-EDISON-KEY-HERE\n' >"$fx/placeholder.env"
chmod 600 "$fx/placeholder.env"
# Not a key: 22 characters of the word "fixture", at a mode the preflight must reject.
printf 'export EDISON_PLATFORM_API_KEY=fixture-not-a-real-key\n' >"$fx/open-perms.env"
chmod 644 "$fx/open-perms.env"

edison_case "missing file"       "$fx/absent.env"      "key file: MISSING"                 1
edison_case "placeholder unreplaced" "$fx/placeholder.env" "key: PLACEHOLDER"              1
edison_case "over-permissive mode"   "$fx/open-perms.env"  "key file: PERMISSIONS TOO OPEN" 1

rm -rf "$fx"
trap - EXIT

echo "== release =="
# The version has to identify the content. This plugin's source is the repo ROOT, so
# `claude plugin update` clones the whole tree — tests, docs and tooling included — and two
# commits declaring the same version but differing in any tracked file are two different
# installs wearing one number. That is not hypothetical: 2026.9.3 was tagged, test-only
# changes merged on top without a bump, and the plugin cache and origin/main both reported
# 2026.9.3 with different bytes. So an already-tagged version must name this exact tree.
pver=$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])' 2>/dev/null)
if [ -z "$pver" ]; then
  err "cannot read version from .claude-plugin/plugin.json"
elif [ -z "$(git tag -l 'v*' 2>/dev/null)" ]; then
  # Silence is not success. A shallow clone with no tags would sail through the branches
  # below by having nothing to compare against, so the missing input is itself the failure.
  # CI checks out with fetch-depth: 0 to give this rule something to read.
  err "no v* tags visible, so the release rule cannot run (CI needs fetch-depth: 0)"
elif ! git rev-parse -q --verify "refs/tags/v$pver" >/dev/null 2>&1; then
  ok "version $pver is not tagged yet — an unreleased bump"
elif git diff --quiet "v$pver" -- . 2>/dev/null; then
  ok "version $pver matches tag v$pver"
else
  err "version $pver is already tagged v$pver but the tree has moved — bump the version. Changed: $(git diff --name-only "v$pver" -- . | tr '\n' ' ')"
fi

echo "== eval guard self-test =="
# These lines RUN tests/eval.sh. If its guard ever regressed they would launch real headless
# sessions and spend tokens from inside `pixi run check` — the exact failure the guard exists
# to prevent, set off by the test for it. So `claude` is shadowed by a stub that spends
# nothing and records every call. The test is then safe when the guard is broken, and it can
# assert the stub was never reached, which is a stronger claim than an exit code alone.
gd=$(mktemp -d "${TMPDIR:-/tmp}/lab-eval-guard.XXXXXX")
trap 'rm -rf "$gd"' EXIT
mkdir -p "$gd/bin"
printf '#!/bin/sh\necho "$@" >>"%s/claude-calls"\n' "$gd" >"$gd/bin/claude"
chmod +x "$gd/bin/claude"

guard_case() { # <label> <eval.sh args...>
  local label="$1"; shift
  local out rc
  out=$(PATH="$gd/bin:$PATH" bash tests/eval.sh "$@" 2>&1)
  rc=$?
  if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q "Nothing was run"; then
    ok "eval guard: $label is refused"
  else
    err "eval guard: $label — wanted exit 2 and a refusal, got exit $rc: $out"
  fi
}

# The four ways to ask for nothing runnable. A bare run is the one that matters most: it is
# what an agent types when it decides to "just run the tests".
guard_case "a bare run"
guard_case "--live on its own" --live
guard_case "an unknown case name" --only nope
guard_case "--only beside --all" --only trigger --all

if [ -s "$gd/claude-calls" ]; then
  err "eval guard: a refused invocation still launched $(grep -c . "$gd/claude-calls") claude session(s)"
else
  ok "eval guard: no refused invocation launched a session"
fi
rm -rf "$gd"
trap - EXIT

echo "== eval assertions =="
# Test the eval regexes without an API call. `--dump` prints the assertions the harness
# actually uses, so this checks THOSE and not a copy that would drift out of step with them.
# Every fixture here is synthetic; several are regressions from a run that was correct and
# was reported as failed.
fixdir=tests/fixtures/eval
dump=$(bash tests/eval.sh --dump 2>/dev/null)
if [ -z "$dump" ]; then
  err "tests/eval.sh --dump printed nothing, so no assertion could be checked"
else
  covered=0
  uncovered=""
  # Heredoc, not a pipe: a piped `while` runs in a subshell, where `err` would set `fail`
  # on a copy of it and every failure below would vanish at the closing `done`.
  while IFS="$(printf '\t')" read -r cname cexp cdeny; do
    [ -n "$cname" ] || continue
    hasfx=0
    if [ -f "$fixdir/$cname.pass.txt" ]; then
      hasfx=1
      if grep -qiE "$cexp" "$fixdir/$cname.pass.txt"; then ok "$cname: pass fixture matches expect"
      else err "$cname: pass fixture does not match its expect regex"; fi
      if [ -n "$cdeny" ]; then
        if grep -qiE "$cdeny" "$fixdir/$cname.pass.txt"; then err "$cname: pass fixture trips its DENY"
        else ok "$cname: pass fixture clears its DENY"; fi
      fi
    fi
    if [ -f "$fixdir/$cname.fail-expect.txt" ]; then
      hasfx=1
      if grep -qiE "$cexp" "$fixdir/$cname.fail-expect.txt"; then err "$cname: fail-expect fixture wrongly matches expect"
      else ok "$cname: fail-expect fixture correctly misses expect"; fi
    fi
    if [ -f "$fixdir/$cname.fail-deny.txt" ]; then
      hasfx=1
      if [ -z "$cdeny" ]; then err "$cname: has a fail-deny fixture but no DENY assertion"
      elif grep -qiE "$cdeny" "$fixdir/$cname.fail-deny.txt"; then ok "$cname: fail-deny fixture trips its DENY"
      else err "$cname: fail-deny fixture does not trip its DENY"; fi
    fi
    if [ "$hasfx" -eq 1 ]; then covered=$((covered + 1)); else uncovered="$uncovered $cname"; fi
  done <<EOF
$dump
EOF
  ok "fixtures cover $covered eval case(s)"
  [ -n "$uncovered" ] && echo "  note: no fixtures yet for:$uncovered"
fi

echo "== eval case lists =="
# Four places name the eval cases: the usage comment, the "no cases matched" line, AGENTS.md
# and tests/README.md. All four were stale before anyone noticed — tests/README.md had been
# missing `reuse-job` through two releases — because keeping them in step was a habit and
# not a check. It is a check now. Lives here rather than in the conformance checker because
# the case list comes from `--dump`, which is this file's business.
if [ -z "${dump:-}" ]; then
  err "no case list to check (tests/eval.sh --dump printed nothing)"
else
  listfail=0
  for f in tests/eval.sh AGENTS.md tests/README.md; do
    [ -f "$f" ] || { err "$f is missing, so its eval case list cannot be checked"; listfail=1; continue; }
    missing=""
    while IFS="$(printf '\t')" read -r cname _rest; do
      [ -n "$cname" ] || continue
      grep -qF -- "$cname" "$f" || missing="$missing $cname"
    done <<EOF
$dump
EOF
    if [ -n "$missing" ]; then
      err "$f does not name these eval cases:$missing"
      listfail=1
    fi
  done
  [ "$listfail" -eq 0 ] && ok "every eval case is named in eval.sh, AGENTS.md and tests/README.md"
fi

echo
if [ $fail -eq 0 ]; then echo "LINT PASS"; else echo "LINT FAIL"; fi
exit $fail
