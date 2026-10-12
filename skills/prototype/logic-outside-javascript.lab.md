# Logic Prototype Outside JavaScript

A lab page with no upstream counterpart. It changes how [LOGIC.md](LOGIC.md) builds a logic
prototype in a repo that is not a JavaScript codebase, such as a Python or R analysis repo.
The rest of LOGIC.md still applies: the question, the module's shape, the scenarios and the
hand-over.

LOGIC.md puts the logic in a `<script>` block so that it can lift into the real code. In a
Python or R repo a JavaScript module cannot lift, so the logic that ships would not be the
logic that was checked. So:

1. **Write the pure module in the repo's language**, next to the code it prototypes for and
   named as a prototype: `prototype_<topic>.py` in a Python repo, `prototype_<topic>.R` in
   an R repo. Pick its shape as LOGIC.md step 2 does, and keep it as pure: no file reads or
   writes, no printing and no plotting inside it.
2. **Drive it from a scenario script or notebook**, in place of the HTML page. The question
   from LOGIC.md step 1 opens it, printed or in the first cell. Each walkthrough from step 3
   becomes a named scenario that resets to a known initial state, applies its actions in
   order and prints the full state after every action. One command runs every scenario,
   such as `python <path>`, or the notebook runs top to bottom.
3. **Build the HTML page only when a non-developer must click through it.** Build it as
   LOGIC.md step 3 describes, as an extra. Its script carries a JavaScript copy of the rules
   for clicking; the module in the repo's language is still the one that lifts.
4. **Capture it** as LOGIC.md step 5 says, with the scenario script or notebook in the place
   of the HTML shell: the module lifts into the real code, and the script or notebook goes to
   the throwaway branch.
