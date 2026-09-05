# lab-edison — cited answers from the Edison platform

Edison is FutureHouse's research platform. It reads the published
literature and answers with citations. It can also run code on a dataset
you upload. This skill drives it from your machine through the
`edison-client` package.

No cluster is involved. This is the one skill in the plugin that talks
only to a cloud service.

## You ask for it by name

The skill never loads on its own. The other three trigger from what you
say; this one waits. Call it yourself:

```text
/lab-compute:lab-edison what is known about ...
```

Every run spends credits from your own account. That is why nothing here
starts without you.

!!! note "Other agent tools"
    The setting that holds the skill back is Claude Code's own. Cursor,
    Codex and the rest ignore it, so there the skill can load like any
    other. It still refuses to run without a key, and it still shows you
    the job before it sends one.

## Your key, and where it goes

You need an Edison API key. It lives in one file on your own machine:

```text
~/.claude/compute/edison.env
```

Write the file, then open it in your editor and paste your key in place
of the placeholder:

```bash
mkdir -p ~/.claude/compute
printf 'export EDISON_PLATFORM_API_KEY=PASTE-YOUR-EDISON-KEY-HERE\n' \
  > ~/.claude/compute/edison.env
chmod 600 ~/.claude/compute/edison.env
```

That is the same thing as copying
[`templates/edison.env`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/edison.env),
which has the reasoning in its comments. The variable name is exact: the
client reads that one and no other. The `chmod` matters too. It leaves
the file readable by you and by nobody else on the machine.

The key sits **beside** `personal.md`, never inside it. An agent reads
`personal.md` into the chat, so a key written there would be copied into
every transcript you ever record.

Before it does anything, the skill checks that file. If it is missing,
still holds the placeholder, or is readable by other people, the agent
stops and says which check failed. It offers to write the file for you,
with the placeholder in place. Then it hands the file back to you.

It will never ask you to type or paste your key into the chat.

## What happens before it spends

- **You see the job and the query.** The skill names the agent it picked
  and prints your question in full, before the task goes out.
- **The costly runs need your OK.** A deep literature run, a data
  analysis run, and any batch of more than three tasks all stop and ask.
- **A follow-up continues the last task.** It rides on the run you just
  read instead of paying again for the same background.

No prices appear anywhere in this repo. They change, and a stale number
is worse than none at all. Check the balance on the platform when the
cost matters.

## Which agent answers which question

| You are asking | What it picks |
| --- | --- |
| A question the published papers can answer, with citations | The literature agent |
| The same, but the papers disagree and it needs real reasoning | The deeper literature agent — slower, and dearer |
| Has anyone done this before? | The precedent agent |
| Chemistry: molecules, properties, how to make one | The molecules agent |
| Something about a dataset you supply | The analysis agent |

Ask in plain words and the skill picks for you. Say which one you want
and it uses that.

## Kosmos runs in your browser

Kosmos is the platform's heavyweight agent, and the API cannot start
one. The client package carries no name for it, so there is nothing to
send. The skill tells you that up front, before it calls anything.

What it can do is get you ready. It drafts the research goal with you,
and it checks your data is in a shape Kosmos can use. A Kosmos run costs
far more than an ordinary task, so the time spent getting ready pays for
itself. You start the run yourself on the platform.

## Where your data sits

The default is your own machine. Your key belongs there and nowhere
else.

- **Data on your laptop.** Nothing to arrange. It uploads and runs.
- **Data on arc.** The skill brings the files down first, then uploads
  from your machine. Your key stays off the shared cluster.
- **Data on ircbc.** Edison cannot be reached from that cluster at all.
  Its compute nodes have no route out. The skill says so and stops,
  rather than hunting for a way around it.

You can run Edison on arc, but only after you put the key there
yourself, in your own session. The skill will not do it for you. It
never copies your key anywhere — not to a cluster, not into a job
script, not onto a command line.

## The first run is slow

The client is never installed into anything you maintain. It runs from a
throwaway environment, so it cannot break your pixi setup, and an active
pixi shell does not disturb it.

The cost is the first run on a new machine. Dozens of packages download
before your question is even sent. It can look hung for a minute or two.
It is not. Every later run reads from the cache and starts at once.

## How you start it

Type `/lab-compute:lab-edison` and then your question. Some examples:

- "Search the literature for what is known about …"
- "Has anyone already done this experiment?"
- "Analyse this table and tell me what it shows."
- "Set up my Edison key on this machine."
