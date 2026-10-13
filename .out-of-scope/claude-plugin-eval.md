# Claude Code's native eval framework

The lab's eval cases stay in `tests/eval.sh`. They do not move to `claude plugin eval`.

## Why this is out of scope

The lab runs its skills in three agents: Claude Code, Codex and Kimi Code. `claude plugin eval`
drives Claude Code only, and nothing in it can start another agent. A case written for it is
a Claude Code case for good.

`eval.sh` also runs only `claude -p` today. It is a shell script, though, so a case can grow a
Codex or Kimi Code run beside the Claude Code one. Gaps that only those two agents showed have
already reached the issue tracker. The harness the lab builds on has to be one that can test
them.

## What a test run showed

Checked on 2026-10-12 with Claude Code 2.1.296, for whoever revisits this:

- A case prompt can call a user-invoked skill with a slash command, such as `/lab-edison`.
- A case cannot run in plan mode. No case setting chooses a permission mode.
- The run's trace leaves out the skill text a slash command loads, so grade the answer.
- A path target tests the working tree, with no push and plugin update first.

## When to revisit

If the framework learns to drive other agents, or the lab settles on Claude Code alone.

## Prior requests

- #87: "Claude Code's native eval framework appears generally available"
