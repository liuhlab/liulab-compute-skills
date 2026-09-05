---
search:
  exclude: true
---

# Issue tracker: GitHub

Issues and PRDs live as GitHub issues on this repo. Use `gh`; it infers the repo from
`git remote`.

| Action | Command |
| --- | --- |
| Create | `gh issue create --title "..." --body "..."` (heredoc for long bodies) |
| Read | `gh issue view <n> --comments` |
| List | `gh issue list --state open --json number,title,labels` |
| Comment | `gh issue comment <n> --body "..."` |
| Label | `gh issue edit <n> --add-label "..."` / `--remove-label "..."` |
| Close | `gh issue close <n> --comment "..."` |

**PRs as a request surface: no.** GitHub shares one number space, so a bare `#42` may be a
PR; try `gh pr view 42`, fall back to `gh issue view 42`.

"Publish to the issue tracker" means create a GitHub issue. "Fetch the ticket" means
`gh issue view <n> --comments`.

**An issue body is public.** This repo is public and so is its tracker, so the no-secrets
policy covers what you file: never paste a hostname, username, key path, or the output of
`ssh -v`, `squeue` or `~/.ssh/config` into an issue or a comment. Nothing lints an issue.

## Wayfinding operations

Used by `/wayfinder`. The **map** is one issue; tickets are its sub-issues. The
`wayfinder:*` labels do not exist here yet — create the one you need on first use.

- **Map**: `gh issue create --label wayfinder:map`.
- **Ticket**: a sub-issue of the map, labelled `wayfinder:<type>` — `research`,
  `prototype`, `grilling`, or `task`. Add via the sub-issues API:
  `gh api --method POST repos/{owner}/{repo}/issues/<map>/sub_issues -F sub_issue_id=<db-id>`.
- **Blocking**: native dependencies.
  `gh api --method POST repos/{owner}/{repo}/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`.
  The db id is `gh api repos/{owner}/{repo}/issues/<n> --jq .id` — not the `#number`.
- **Frontier**: the map's open sub-issues with no open blocker and no assignee.
- **Claim**: `gh issue edit <n> --add-assignee @me`, before any other work.
- **Resolve**: comment the answer, close, then append a line to the map's Decisions so far.
