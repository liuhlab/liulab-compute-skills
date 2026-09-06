---
search:
  exclude: true
---

# The Edison skill's spend path became a Python package

`skills/lab-edison/scripts/edison-task.sh` is gone. Submitting, polling, recovering,
cancelling and fetching, the Kosmos chat surface, dataset upload and the preflight live in
`src/edison_cli/` and run from the repo's pixi environment.

## Why a package, and not a bigger script

Not because bash was the wrong language. The script was bash dispatch around a single
133-line Python heredoc, and most of what was wrong with it was fixable in place.

The reason is that no gate here had ever read that Python. `ruff` and `pyright` see `.py`
files; the heredoc is inside a `.sh`, and shellcheck stops at its delimiter. The lines that
spend a lab member's credits were the only unreviewed code in the tree.

Two things only a module does well: the Kosmos stop protocol, a stateful sweep — queue the
halt, then cancel the stragglers — rather than one call, and typed responses, so a reply read
out of `tool_calls[].function.arguments` is written once.

## Why pixi

The client was reached ephemerally under `uv`, so a lab member maintained nothing. It is now a
dependency of the **default** environment, because pyright cannot check a call it cannot
resolve. The cost is real: over a hundred transitive dependencies in a lock that held no PyPI
packages, installed on every CI run, and a first Edison command that builds an environment —
again after every plugin update, which writes a fresh directory rather than refreshing one.

## Rejected

**A separate `edison` feature.** Keeps the lock small; puts the client outside the environment
pyright runs in.

**A standalone stop script.** A second implementation of queue-then-sweep, exercised only in an
emergency. `kosmos start` prints the stop command instead.

**Pointing `--manifest-path` at the marketplace clone.** A real git repo, at a path that
survives updates. It is also the catalogue and not the installed plugin, so the Python that ran
would not be the Python that was installed.

## What this reverses

`pyproject.toml` said this repo ships no package and refused a `fallback-version`. It now ships
one it never publishes, and needs the fallback: the installed plugin is a plain copy with no
`.git`, so `source = "vcs"` resolves no version there and the install dies.

The `docs` environment left the default solve group and took `no-default-feature`. zensical's
conda pins otherwise exclude every `edison-client` above 0.11.1 — which cannot be imported.

`docs/adr/0010` said the preflight is not folded in. It now is, with the constraint that its
module imports only the standard library, so the no-secrets sweep needs no dependency at all.
