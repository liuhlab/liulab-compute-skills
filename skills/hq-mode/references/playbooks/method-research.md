# Method research

**You own an explanation a bench biologist can act on, and every claim's source.**

1. Gather the papers, supplements and vendor protocols into the repo's reference dir, one
   folder per topic with a README. Dump PDFs and spreadsheets to text on first read.
2. One research subagent per source (`/research`). Each returns cited claims with an evidence
   tier.
3. Explain the mechanism in plain words, step by step, every abbreviation defined. Add the
   numbers that decide feasibility: capacity, yield, cost per sample, time.
4. When the lab's design differs from the published one, go point by point: what they did, what
   we change, why, and the evidence.
5. Two independent checkers: one for the facts against the sources, one for the reasoning,
   neither assuming the design works.
6. Answer "I don't understand X" in the terminal until it is clear. Then write a local HTML
   report with diagrams of the critical steps, run `unslop`, and open it in the browser.
7. Post a plain-language summary to a GitHub Discussion when the repo keeps one.

**Reply:** the one best answer, not a menu; the report's path; open questions only a bench
test can settle.
