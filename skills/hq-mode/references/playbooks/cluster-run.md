# Cluster run

**You own the run's correctness and the cluster's goodwill.** `lab-hpc` owns every cluster
fact; read it first.

1. `lab-hpc` step 0. Work happens on a compute node, never the login node, and the host rule
   goes into every subagent brief.
2. Check for prepared inputs: registered genomes and indexes, the shared data root, the lab's
   data packages. Don't re-download what is there.
3. Write the sbatch scripts: one unit as a pilot (one sample, one chromosome, a small
   subsample), then the full set. Outputs and logs go to scratch or the project's output root,
   never the home directory and never the reference data root.
4. Show the exact scripts and wait for the user's yes before any `sbatch` or `srun`, the pilot's
   included. "Land it" and "going to bed" don't change this: prepare everything else, then end
   the turn on the question.
5. Run the pilot. Time it and extrapolate. Give the user the estimate before scaling.
6. Fan out: separate units become separate jobs or an array, never a serial loop. Check each
   unit as it finishes; don't wait for the last.
7. On a misbehaving job, name the symptom and propose the workaround (exclude a node, resubmit
   one unit), and wait for a yes. Never `scancel` a job you didn't start.
8. Verify outputs, not exit codes: sizes, counts, a spot check against the pilot.

**Reply:** what ran where, the pilot's numbers and the extrapolation, per-unit status as a
checklist, outputs and their location, anything left queued.
