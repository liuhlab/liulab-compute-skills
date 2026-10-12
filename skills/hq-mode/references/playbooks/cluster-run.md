---
search:
  exclude: true
---

<!-- Evidence: medium. Reference-genome registration as parallel jobs, small case first then
scale, scratch not home, host rule in every brief (science slice, ~30). -->

# Cluster run

**You own the run's correctness and the cluster's goodwill.** `lab-hpc` owns every cluster
fact; read it first.

1. `lab-hpc` step 0. Work happens on a compute node, never the login node, and the host rule
   goes into every subagent brief.
2. Check for prepared inputs: registered genomes and indexes, the shared data root, the lab's
   data packages. Don't re-download what is there.
3. Run one unit as a pilot: one sample, one chromosome, a small subsample. Time it and
   extrapolate. Give the user the estimate before scaling.
4. Write the sbatch script. Outputs and logs go to scratch or the project's output root, never
   the home directory and never the reference data root. Show the exact script and get a yes.
5. Fan out: separate units become separate jobs or an array, never a serial loop. Check each
   unit as it finishes; don't wait for the last.
6. On a misbehaving job, name the symptom and propose the workaround (exclude a node, resubmit
   one unit). Never `scancel` a job you didn't start.
7. Verify outputs, not exit codes: sizes, counts, a spot check against the pilot.

**Reply:** what ran where, the pilot's numbers and the extrapolation, per-unit status as a
checklist, outputs and their location, anything left queued.
