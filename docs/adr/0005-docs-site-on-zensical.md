---
search:
  exclude: true
---

# The docs site is built by zensical, pinned exactly

`mkdocs.yml` is now built by `zensical`, pinned `==0.0.57` in the `docs` pixi feature, not
by mkdocs plus mkdocs-material. zensical reads the same `mkdocs.yml` and runs the same
Python-Markdown extensions, so the config stays portable. The site builds strictly on every
pull request (the `docs` job in `ci.yml`) and publishes from `main` only.

## Why this is surprising

zensical is a `0.0.x` alpha, and the lab's research note **declined it for production
repos**. The reason to take it here anyway is not that the note was wrong: it is that every
lab repo should be on **one builder**, and this repo is where paying for that costs least.
The whole site is five hand-written pages with nothing generated, so a bad release means a
rebuild rather than a rewrite, and reversal is two lines in `pyproject.toml` plus dropping
the zensical-only `validation:` keys. The repos the note was protecting keep mkdocs-material
until this one has run on the alpha for a while.

## What it costs

- **No `gh-deploy`, and none is planned.** `.github/workflows/docs.yml` builds `./site` and
  publishes it with `peaceiris/actions-gh-pages@v4` and `force_orphan: true` — one commit on
  `gh-pages`, replaced whole, which is what `mkdocs gh-deploy --force` already did.
- **`exclude_docs:` is silently ignored.** Every file under `docs/` is published whether or
  not anything lists it. Agent-facing pages therefore carry `search: exclude: true` front
  matter *and* stay out of `nav:`. Front matter does nothing about the navbar; `nav:` does
  nothing about search. Both, always. Measured on this tree: the eight pages under
  `docs/adr/` and `docs/agents/` appear zero times in `search.json`, zero times in
  `sitemap.xml` and zero times in the navbar, and each is still reachable by URL.
- **`--strict` validates links, not the `nav:`.** An entry naming a missing file builds
  green and publishes a menu item that 404s. No setting turns that back on, so conformance
  rule `nav-target-exists` is what has to catch it. The note is beside the `nav:` a
  maintainer edits.

## Why the pin is exact

`0.0.x` promises nothing about `0.0.58`, and a patch release has already broken search once.
Bump the pin in a commit of its own and re-run `pixi run docs-build`.
