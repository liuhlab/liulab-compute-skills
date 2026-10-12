# Improve a metric

**You own the metric and the experiment's integrity.**

1. Fix one metric, the direction that is better, and a stop predicate: a target plus a minimum
   number of attempts.
2. Build the measurement, prove it separates good from bad cases, then freeze it. Record the
   baseline and a green gate before any change. Vet it with `references/benchmark-checklist.md`.
3. Keep a decision log: one row per attempt, with hypothesis, change, before, after, verdict.
4. One change, one measurement, keep or revert. Never stack untested changes. Delegate each
   attempt to a subagent in its own worktree.
5. For an analysis metric, never tune on the data you report on; hold a set out.
6. Push past the first plateau before stopping. Don't relax the predicate.

**Reply:** baseline to final, attempts kept and reverted, the log's path, the next idea.
