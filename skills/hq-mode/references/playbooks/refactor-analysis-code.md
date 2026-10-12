---
search:
  exclude: true
---

<!-- Evidence: medium-thin. "Confirm results are unchanged" (science slice, 4); architecture
passes via /improve-codebase-architecture (5 runs). -->

# Refactor analysis code

**You own the outputs. The structure changes; the results don't.**

1. Pin the outputs on a fixture first: a small input and its saved outputs, compared exactly or
   within a stated tolerance. Type checks and lint are not a pin.
2. Stages that checkpoint to disk are the execution plan; keep them. Move the rules they share
   (formats, thresholds, sample-sheet parsing) into one module they import.
3. Subtract before you add: dead code, one-caller wrappers, vestigial files.
4. Small steps, the pin green after each. Migrate every caller and delete the old path in the
   same change.
5. Prove the results unchanged on real data, not only the fixture.
6. A refactor session refactors. Bugs and features it finds become tickets.

**Reply:** what changed shape, the pin, the equivalence proof, and what you deleted.
