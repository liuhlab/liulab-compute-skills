## Remote compute (lab HPC) — always applies

- I work on lab HPC clusters (arc/chimera, ircbc). Before ANY ssh, Slurm, or
  remote-compute step, load the `lab-hpc` skill (plugin `lab-compute`) for
  cluster details, aliases, and workflow.
- Hard rule even if the skill isn't loaded: **never run compute on a login
  node** — get a Slurm job first.
- If ssh to `ircbc` hangs or times out: **stop and tell me to check the VPN.**
