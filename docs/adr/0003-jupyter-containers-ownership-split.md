---
search:
  exclude: true
---

# lab-jupyter owns the session; lab-containers owns the container command

Running Jupyter on ircbc needs two subjects at once: a Slurm session lifecycle, and a
Singularity invocation. Either skill could have carried the whole recipe. The split is:

- **`lab-jupyter`** owns the lifecycle — reuse, submit, token, tunnel, cleanup — with the
  per-cluster differences parameterized in its table.
- **`lab-containers`** owns the container invocations, including the ircbc Jupyter sbatch
  command.

Neither repeats the other's half. `lab-jupyter`'s table sends the reader to
`lab-containers` for that one command, to be taken verbatim.

## Why the seam is the sbatch line

That is where the two subjects actually meet. Everything above it — find a running job,
poll until it starts, grep the token, open the tunnel, clean up — is the same on both
clusters and belongs to the session. Everything inside it is container detail that changes
when the image, the proxy environment or the activation script changes, and belongs to the
container recipe.

The alternative was each skill carrying a complete ircbc Jupyter recipe. That is two copies
of one sbatch command, in two files edited by different tasks, and they drift. The copy
that drifts first is the one nobody ran that week, which is also the one an agent picks
next.

## What it costs

Neither page is self-contained for the ircbc case: an agent following `lab-jupyter` has to
open `lab-containers` mid-procedure. That is the price of not having two copies, and it is
paid once per session.

**Verbatim is load-bearing.** A reader who paraphrases the sbatch into `lab-jupyter` has
re-created exactly the duplicate this split exists to prevent — and it will look correct,
because it was correct on the day it was copied. The `jupyter-ircbc` eval case pins that
the handoff works end to end, so a broken pointer fails as a behavior, not just as a
missing link.

The split is a convention, not a mechanism: nothing in the gate stops someone pasting the
command into the wrong file. Keeping it is a review habit, which is why the reason is
written down rather than left as a layout that looks arbitrary.
