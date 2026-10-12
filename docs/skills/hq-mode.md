# hq-mode: work through a whole task the lab's way

Type it at the start of a task, followed by what you want:

```text
/hq-mode analyse the new run and tell me if the batch effect is gone
```

It never starts on its own. You turn it on, in Claude Code, Codex or Kimi Code.

## What it does

First the agent reads one page of working rules. They cover when to ask you and when to
find the answer itself, what it may do without asking, how it splits work between helpers,
and how it writes its reply. A rule in your repo's own `AGENTS.md` wins over that page.

Then it picks the playbook that fits your task and copies its steps into its to-do list, so
you can see what it will do and how far it has got. There are 17:

| Kind | Playbooks |
| --- | --- |
| Science | analysis, cluster run, method research, experiment plan, figure |
| Writing | paper section, grant section, talk, review a document, message |
| Code | land the tickets, improve a metric, refactor analysis code, investigation |
| Any task | long run, close the session |

When none fits, it designs one for the task, writes the steps down, and works through them.

It also knows which skill to reach for along the way: the lab cluster skills before any
ssh, `unslop` before you read its prose, and the planning skills such as `/grill-with-docs`
and `/to-spec` for a new idea. A skill you start by typing its name stays yours to start. The
agent suggests it rather than running it.

## What it always asks first

Some steps wait for your yes, every time:

- submitting, running or cancelling a Slurm job, after it shows you the exact script;
- spending Edison credits;
- writing to or deleting from the lab's shared package store;
- force-pushing, or deleting data;
- merging a pull request nobody reviewed, unless you told it to land it;
- anything on a live service;
- making private work public;
- wet-lab steps;
- editing your own document beyond what you asked for.

This list wins over everything else you say in the session. "I'm going to bed, land it" lets
the agent keep going on its own. It still stops at a Slurm job and waits for you, and you
find the script ready in the morning. "Close the issue" is not "merge it".

## Where the rules came from

They are the lab's way of working, drawn from many real sessions and written as "the user",
so they apply to whoever types `/hq-mode`. Several playbooks build on
[pstack](https://github.com/cursor/plugins/tree/main/pstack)'s `poteto-mode`, and the
planning flow follows [mattpocock/skills](https://github.com/mattpocock/skills). Both are MIT
licensed.
