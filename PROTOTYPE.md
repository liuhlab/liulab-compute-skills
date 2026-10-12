# PROTOTYPE: hq-mode, first draft

Throwaway. This branch answers one question for the map *Lab skill set: tracked upstreams, lab
edits, one install path*: what does the mode route to, and how is it shaped? Never merge it.
The decision lands on the ticket; the real skill gets built later from tickets.

## What is here

- `skills/hq-mode/SKILL.md`: the router, under the repo's 600-word cap for a skill body.
- `references/working-style.md`: the rules every turn follows.
- `references/principles.md`: the index of the 22 forked pstack principles.
- `references/playbooks/`: 16 playbooks plus the `figure-it-out` fallback. Each opens with a
  comment saying how much mined evidence stands behind it.

Not drafted: the 22 principle pages, `benchmark-checklist.md`, `show-me-your-work.md` (pstack
forks, copied at build time), and Codex's `agents/openai.yaml`.

## Sources

- The shape: pstack `poteto-mode` and `figure-it-out` at `978ca6e`; mattpocock `ask-matt` at
  `49dd158`.
- The rules: the maintainer's own agent sessions, mined the way pstack's `automate-me` does
  (four slices: a large science-code repo, other science repos, writing and grants, lab
  infrastructure; about 2,800 typed prompts, 450 Codex prompts, 80 memory files, and the agent
  docs of 15 repos). A rule went into `working-style.md` only if it showed up in at least two
  slices. Mining notes stay off this public branch.
- The decisions already on the map: what comes in and in what form, the pstack review, the
  always-pause list, and the bias pass's provisional principle edits.

## Choices to react to

1. The 600-word cap moves `poteto-mode`'s inline sections into `working-style.md`, one more
   read per session.
2. How the mode turns on: user-invoked, plus a line in each agent's user-level file telling it
   to read the working-style page for any non-trivial task.
3. The playbook set, which leans on writing because the sessions do.
4. Lab defaults in the mode, not only in the repo template.
5. The merge rule: merge your own PR when told to land it; a loose "close it" is not enough.
