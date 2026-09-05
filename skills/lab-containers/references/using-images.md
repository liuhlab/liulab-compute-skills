# Using the lab container images

Verified patterns for running work inside a `liulab-runtime` SIF on ircbc, where Singularity is an
old 3.x (`module load singularity && singularity --version` reports the exact build). Getting or
refreshing an image: `SKILL.md`, then `references/update-image.md`.

All of this is compute-node work — none of it belongs on the login node. Activation inside the
container is always `source /app/.pixi/activate-<env>.sh` (fallback:
`export PATH=/app/.pixi/envs/<env>/bin:$PATH`). Do **not** use `singularity run`; the image's
Docker entrypoint does not work under this old Singularity. Singularity is module-only, never on
PATH, and `module load singularity` works fine in a plain non-interactive ssh command. `$HOME` is
auto-bound (re-verified 2026-07-05); add `--bind /share/lhqlab` or other data dirs as needed.

The `<command...>` slot sits two quoting levels deep — write any inner double quote as `\\\"`, or
keep the payload quote-free. Worked example in `references/update-image.md`.

Already holding a compute node? Drop the `ssh ircbc '…'` wrapper and run the `srun` or `sbatch`
there; the whole Slurm client works from ircbc compute nodes.

## Run a command in a compute job

```bash
ssh ircbc 'srun -p compute_cpu -t <time> -c <cpus> bash -c "\
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash -c \"source /app/.pixi/activate-<env>.sh && <command...>\""'
```

## Interactive shell in the pixi env, straight from the local PC

`--rcfile` gives an activated interactive shell and skips the host bashrc:

```bash
ssh -t ircbc 'srun -p compute_cpu -t <time> -c <cpus> --pty bash -c "\
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash --rcfile /app/.pixi/activate-<env>.sh"'
```

## Jupyter Lab in the container

The session lifecycle — reuse an existing job first, then node, token, tunnel, cleanup — belongs
to `lab-jupyter`. This skill owns only the ircbc submit command (`<port>`: default 9990, see
lab-jupyter). Show it to the user and get confirmation before submitting; `sbatch --test-only` is
a safe non-submitting dry run to show alongside it.

```bash
ssh ircbc 'sbatch -p compute_cpu -t <time> -c <cpus> -J jupyter \
  -o $LIU_LAB_PACKAGES/logs/jupyter.%j.log --wrap "\
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy; \
  module load singularity && \
  singularity exec --bind /share/lhqlab $LIU_LAB_PACKAGES/liulab-runtime_<env>.sif \
    bash -c \"source /app/.pixi/activate-<env>.sh && jupyter lab --no-browser --port=<port> --ip=127.0.0.1\""'
```

The `-o` path is the token source. Node, token, tunnel and cleanup: `lab-jupyter` steps 1–5 —
its parameter table carries the ircbc squeue form, log path, and tunnel target.
