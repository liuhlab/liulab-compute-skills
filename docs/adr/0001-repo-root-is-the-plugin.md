---
search:
  exclude: true
---

# The repo root is the plugin, and one plugin holds every skill

`.claude-plugin/marketplace.json` declares `source: "./"`, so the repo root *is* the
plugin: marketplace `liulab`, plugin `lab-compute`, and every skill under `skills/` inside
that single plugin. A marketplace may declare several plugins from subdirectories, and this
one deliberately does not.

## Why one plugin

The skills are not independent. `lab-jupyter` takes an sbatch command verbatim from
`lab-containers`; both defer to `lab-hpc` for the preflight, the alias vocabulary and the
safety rules. A machine carrying `lab-hpc` at one version and `lab-containers` at another
is a combination nothing here tests and nobody would think to check — the failure shows up
as an agent running a command against a cluster, which is the worst place to find it.

One plugin makes the update atomic. `claude plugin update lab-compute@liulab` moves all of
the skills or none of them, so the version on a machine is one number and a cross-reference
is always answered by the copy it was written against.

## What it costs

- A user who wants only the Jupyter recipe installs all of them. Cheap: the skills are
  Markdown, and an unused description costs only its share of the trigger listing.
- Every description loads on every machine that installs the plugin, so adding a skill
  spends a little of everyone's context whether they use it or not. That pressure is real
  and is what keeps the descriptions keyword-dense instead of chatty — but it is judgement,
  not a threshold: the 1536-character limit caps one description, never their sum.
- Splitting later means a new plugin name, which every installed machine has to install by
  hand. Reversal is not free, which is why this is recorded.

## Why the root, rather than a subdirectory

A subdirectory plugin would put the skills one level down and leave the root as packaging
around them. There is nothing else in this repo to package: the tests, the docs and the
templates all exist to serve the skills. Making the root the plugin means the thing you
clone and the thing you install are the same tree, with no path prefix to keep in step
between the manifest and the layout.
