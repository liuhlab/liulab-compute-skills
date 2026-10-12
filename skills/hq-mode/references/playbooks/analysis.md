---
search:
  exclude: true
---

<!-- Evidence: thin. Before/after-with-numbers and "results unchanged" recur (2 slices, ~10);
the analysis itself is rarely in the logs. Drafted mostly from the ticket and the bias pass. -->

# Analysis

**You own the number and whether it means what you say.**

1. State the question as a result you could be wrong about, and the check that would show it:
   a known truth, a control, a held-out set. Fix the criterion before you see the result.
2. Name the data shape: what one row, one sample and one batch are. Find the reference data
   already on disk before downloading anything.
3. Pilot on a subsample. Check row counts after every join and filter, and NA and range counts
   at each step: a silent row drop is the commonest wrong answer.
4. Run it in full, locally or in an existing job. A new `sbatch` → **cluster-run**.
5. Before you report the number: what bounds it, and what else could produce it (leakage,
   batch confounding, duplicated samples, a filter that changed the denominator). Read
   **explain-the-number**.
6. If you compared alternatives (a normalisation, a parameter), report every one you tried, not
   only the best.
7. Show it: a figure (**figure**) or a table, opened and looked at before you report.

**Reply:** the question, the answer with its evidence label, the checks it passed, what you
tried and dropped, and the next check you would run.
