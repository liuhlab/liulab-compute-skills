# My lab compute specifics

<!--
Machine-local per-user config. Copy this file to ~/.claude/compute/personal.md
and fill it in. NEVER commit it to any repo. Do NOT put IP addresses, keys,
or passwords here either — connection details belong in ~/.ssh/config only.
-->

- arc/chimera username: `<you>`
- ircbc username: `<you>`
- arc code dir: `/large_storage/zhoulab/<you>/pkg`
- ircbc code dir: `/share/home/<you>/src`
- Jupyter port (lab-jupyter default 9990): ...
- Jupyter launch command on arc (absolute path — sbatch does not load your
  env manager): ...
- My usual Jupyter job resources (--cpus-per-task / --mem / --gpus /
  --time): ...
- My reservation / sbatch notes: ...
- My persistent interactive job, if any (e.g. a long-lived job on an arc
  preemptible/priority partition): partition, the ssh-config node alias, and
  "reuse it first." If it exists, most interactive work can go straight to
  that node — `ssh <node-alias>` instead of allocating a fresh job. (Node
  aliases live in ~/.ssh/config, never here.) ...
- Anything else agents should know about MY setup: ...
