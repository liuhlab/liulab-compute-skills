# Tunnel and token detail

Companion to `SKILL.md` steps 3 and 4. Read it when the local port is already taken, when the tunnel
comes up but Jupyter does not answer, or when no token appears in the job log.

## The local port is busy

`lsof -nP -iTCP:<port> -sTCP:LISTEN` printed something. Find out what it is before touching it:

```bash
ps -o pid=,command= -p "$(lsof -tnP -iTCP:<port> -sTCP:LISTEN)"
```

- An ssh tunnel to the **same** node → reuse it as it stands; just hand over the URL.
- An ssh tunnel to a different or dead node → `kill <pid>`, that PID and no other, then re-tunnel.
- Anything else — another Jupyter, a dev server, something you do not recognise → leave it running
  and pick a different local port: `ssh -f -N -L <newport>:localhost:<port> <node>`.

Never `pkill ssh` to clear a port. It kills tunnels and sessions this flow does not own.

## The tunnel is up but Jupyter does not answer

`curl -s http://localhost:<port>/api` should return `{"version": ...}`. If it hangs or refuses:

- Re-probe the node — `ssh <node> 'ss -tln | grep -E "127\.0\.0\.1:<port>"'`. Still listening?
  The tunnel died; kill its PID and re-run step 4.
- Nothing listening → check the job (`squeue --me` from a node you hold, `ssh arc '<same>'`
  otherwise). `zhoulab_gpu_priority` is `PreemptMode=REQUEUE`, so a preempted Jupyter job comes
  back on a **different node with a new token** — redo steps 3 and 4 against that node.
- The job is gone entirely → back to step 2, with the user's confirmation.

## Getting the token

The log line to look for is `http://127.0.0.1:<port>/lab?token=<token>`.

- **A job you just submitted, either cluster** → grep its log (path in `SKILL.md`'s table):
  `grep -m1 "?token=" sbatch/jupyter.<jobid>.log`, run from the node you hold or via
  `ssh arc '…'`. Allow 10-30 s: the line is written only once Jupyter finishes starting.
- **A job you reused, arc** → it may log somewhere you cannot guess, so ask the running server
  instead: `ssh <node> 'bash -lc "<jupyter> server list"'`. The login shell is what makes
  user-installed tools visible; a plain `ssh <node> '<jupyter> server list'` will not find them.
- **ircbc, always** → grep the job log. Jupyter runs inside the SIF, so there is no Jupyter on the
  node itself for `server list` to ask.
- **Still nothing** → do not restart the server blind. Show the user the tail of the log
  (`tail -20 <log>`) and let them decide; a container or environment error usually sits right there.

A token is a credential. Put it in the URL you hand the user, and keep it out of files, commits and
anything shared.
