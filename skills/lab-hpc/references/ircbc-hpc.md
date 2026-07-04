# ircbc_hpc — CPU-only cluster (old OS; Singularity required)

CPU-only Slurm cluster running **CentOS 7 with glibc 2.17**. Modern binaries
will NOT run on the bare OS — always run real work inside **Singularity**
with the lab's `ghcr.io` container images. All hosts below are
**`~/.ssh/config` aliases** — resolve usernames/hostnames from that file (see
the skill's step 0); never record them.

## VPN — read this first

The whole cluster sits behind a **VPN** (atrust app) that the user manages
manually. If ssh to `ircbc` (or any of its nodes) hangs or times out:
**stop immediately and tell the user to check / re-login the VPN.** Do not
retry in a loop, do not try alternate routes, do not attempt to fix the VPN.

## Hosts

- **Login:** `ircbc`. Light work only: editing, git, Slurm commands. **No
  compute.**
- **File transfer:** `ircbc-transfer` (note: this alias uses a separate,
  shared lab account — whatever is configured in the user's `~/.ssh/config`).
- **Compute nodes:** `cpu01`…`cpu08`, ProxyJump through `ircbc`. Reachable
  **only while the user holds a Slurm job on them**.

## Running work: Singularity + lab containers

Environments are built with pixi and published as containers by the
`liulab-runtime` repo (check its README for current image names and tags).
Typical usage on a compute node:

```bash
# pull once (creates a .sif file)
singularity pull docker://ghcr.io/liuhlab/<image>:<tag>

# run commands inside the container (bind your code/data dirs as needed)
singularity exec --bind /share/home/<user> <image>_<tag>.sif <command...>
```

Never run modern toolchains (recent Python builds, compiled binaries from
elsewhere) directly on the host OS — glibc 2.17 will break them.

## Storage / code

- Code lives in `/share/home/<user>/src`, with the same directory names as
  local repos, synced via git (local → GitHub → `git pull` remote).
