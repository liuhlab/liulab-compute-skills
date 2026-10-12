# Science smells

A lab addition to the smell baseline in `SKILL.md`, for a diff that touches analysis code: a
script, a notebook or a pipeline stage. Fowler's smells are about objects; these are the
defects that change a result. The baseline's two rules bind them too: a documented repo
standard overrides a smell, and each one is a judgement call, never a hard violation.

Each smell reads *what it is* → *how to fix*:

- **Unseeded Randomness**: a sample, split, shuffle, initialisation or stochastic method
  runs with no fixed seed, so a rerun gives a different result. → set the seed once where
  a reader sees it, and record it with the output.
- **Silent Drop**: a join, filter, type coercion or missing-value step removes rows or
  turns values into NA, and nothing reports how many. → report or assert the row and NA
  counts on both sides of the step.
- **Mixed Coordinates**: 0-based and 1-based positions, or half-open and closed intervals,
  meet in one change, such as BED against GTF or VCF. → convert once, where the data comes
  in, and name the convention.
- **Unsourced Threshold**: a cutoff such as a p-value, fold change, minimum count or QC
  limit appears as a bare number with no cited source. → cite where it comes from, or make
  it a named parameter with a comment saying why that value.
- **Hard-coded Absolute Path**: an absolute path to data or output that exists on one
  machine. → take it from a config file, an argument or an environment variable.
- **Cell-order State**: a notebook's result depends on cells run out of order, or on a
  variable an earlier session left in the kernel. → restart the kernel and run top to
  bottom; move what has to persist into a script or module.
