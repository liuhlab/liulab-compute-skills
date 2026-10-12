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

## Verdicts

1. The 600-word cap stays. The core lives in `working-style.md`, read first.
2. User-invoked, plus one always-on line on the lab defaults page that `/lab-setup` points
   each agent at: for any non-trivial task, read the working-style page first.
3. All 17 playbooks stay. The thin ones gain evidence from use.
4. Lab defaults stay in the mode; a repo's own `AGENTS.md` wins.
5. Merge your own PR when told to land it; a loose "close it" is not enough.
