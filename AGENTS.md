# AGENTS.md

This repo keeps a single source of truth for agent guidance in
[`CLAUDE.md`](./CLAUDE.md) — read that file.

Everything there applies to **any** coding agent working in this repo, not
just Claude Code: what the repo is, the hard security policy (no connection
details ever), the `lab-*` naming policy, the commands, the release flow,
and the architecture/editing rules.

Only the tool-specific literals in `CLAUDE.md` are Claude Code's own and
must **not** be renamed for another agent — real filesystem paths
(`.claude-plugin/`, `~/.claude/compute/personal.md`, `templates/CLAUDE-stub.md`)
and CLI commands (`claude plugin …`, `claude -p …`) stay exactly as written.
