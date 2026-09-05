---
search:
  exclude: true
---

# The Edison skill stopped teaching the spend path and shipped it

`skills/lab-edison/scripts/edison-task.sh` owns submitting a task, polling it, listing your own
runs, cancelling one and fetching what one produced. The skill body and the reference pages
point at it. They no longer carry a client call to retype.

## Why a script and not a rule

The one failure this skill exists to prevent is a spent credit whose task id nobody holds.
Until now the thing preventing it was an ordering rule — submit, print the id, only then poll —
spread over two reference pages and re-typed at every submission. It failed in a real session:
a paid run was recovered through task history. A rule that has to be remembered at the moment
of spending is not a safeguard, it is a hope. The ordering is now structure: the id is the
first line of output, before anything in the process can block.

Two more properties come with it. The command runs the preflight itself and relays its remedy,
so a skipped step zero refuses instead of spending — which matters most in agent tools that
ignore `disable-model-invocation` and will load this skill like any other.

## Why submission takes a file

`--query-file`, never an inline string. The artefact the user confirmed becomes a real file,
so "show before you spend" is structural rather than remembered, and what was approved and
what was paid for are the same bytes. An absent or empty file is refused before the network is
touched.

## Rejected

**A dry-run default gated by a flag.** The safety is advisory and the flag is one token away.

**Splitting by cost:** a free read-only helper, with submission left as prose. That is the
observed failure preserved — a rule where the structure should be.

## What is unchanged

The never-transmit property of
`docs/adr/0007-edison-key-file-and-never-transmit.md`. The key is sourced from the key file
into the environment the client inherits: never an argument, never on a command line, never
echoed, never in the program text. The gate asserts all three against a stub, and asserts the
key did arrive, so the absence proves something.

The preflight is not folded in. It keeps its path and shape, so the parallel with the cluster
preflight survives and the read-only check stays separable from the command that spends.
