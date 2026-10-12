---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Where the repo has a `check` task (`pixi run check`), the full run is that task plus the lanes `AGENTS.md` lists outside it. Where there is no test suite, rerun the work on its fixture and diff the outputs against the pinned result.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.
