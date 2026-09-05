---
search:
  exclude: true
---

# The Edison key gets its own file, and the skill never transmits it

The platform API key lives in `~/.claude/compute/edison.env` at mode 600 — its own file,
beside the per-user config and never inside it. A placeholder copy ships in `templates/`.
The skill sources that file into the process that needs the key, and reaches it no other
way.

## Why not the per-user config

`personal.md` is the obvious home and the wrong one. Skills read it *into context*: that is
what it is for, and it is how per-user notes reach an agent at all. A key written there is
copied into the transcript of every session that loads a skill — not through a bug, but
through the file working exactly as designed. A public repo whose hard policy forbids
secrets cannot ship a convention that leaks one by default.

A separate file inverts that. Nothing reads it into context, a shell sources it, and the
value reaches the client as an environment variable without being rendered anywhere.

## Why a placeholder in templates

The same pattern `personal.md` already uses, and templates are documentation rather than
anything the plugin loads. It buys two things: the user replaces one obvious string instead
of inventing a path and a variable name, and the preflight gains a value it can recognise,
so an unreplaced placeholder reports "not configured" instead of failing minutes later as
an authentication error.

## The rule, and what it is not

**The skill never transmits the key.** No scp or rsync, never written into a job script,
never on a command line, never an `api_key=` argument, and never printed — the preflight
reports lengths and verdicts, nothing else. **It never asks the user to type or paste the
key into the conversation**: it writes the placeholder and stops.

The property is *never transmits*, not *never runs on a cluster*. Edison on arc is fine
once the user has installed the key there themselves — their deliberate act, and one the
skill will not perform for them. Stated the other way the rule would be wider than the risk
and unenforceable besides.

## What it costs

`disable-model-invocation: true`, the frontmatter key making this skill user-invoked, is
Claude Code's and not part of the open Agent Skills standard. **Other agent tools ignore it
and will treat `lab-edison` as normally triggerable.** There, "never spends a credit
unprompted" rests on the preflight and the description alone. The README's claim that any
agentic tool can consume these skills is still true, and weaker than it was.
