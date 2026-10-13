# Figure

**You own a figure that says one thing truly, at a size people can read.**

1. Name the one message, and the audience: reviewers, a talk, a paper.
2. Data figures: plot from the data with the repo's plotting code; never redraw a result by
   hand. Prefer an existing library to hand-written SVG or JS.
3. Schematics and illustrations: generate raster candidates (Codex, headless, in a subagent);
   text stays editable outside the image. Use the paper's real panel where one exists. A
   diagram on a docs site follows the docs-page playbook instead.
4. Render 2 to 4 options and show them. The user often takes parts of several; build the
   hybrid.
5. When the user marks a region, change only that region and match the rest's scale and style.
6. Check at final size: fonts large enough for print, nothing overlapping or squeezed, colour
   only where it encodes something. Look at the rendered image yourself first.
7. Keep one final file; alternatives go to `archive/`.

**Reply:** the image path, what changed, and the check at final size.
