# lab-edison: cited answers from the Edison platform

Edison is a research platform, run by Edison Scientific. It answers questions from
the published literature with citations, runs code on a dataset you upload, and in
Kosmos has a research agent that works a whole goal over many rounds. This skill
drives it from your machine through the `edison-client` package. No cluster is involved. It is the one skill here that talks only to a
cloud service.

## You ask for it by name

The skill never loads on its own. The other three trigger from what you say; this
one waits.

```text
/lab-compute:lab-edison what is known about ...
```

Other openings that work: "Has anyone already done this experiment?", "Analyse
this table and tell me what it shows", "Set up my Edison key on this machine."

Every run spends credits from your own account. That is why nothing here starts
without you.

!!! note "Other agent tools"
    The setting that holds the skill back is Claude Code's own. Cursor, Codex and
    the rest ignore it, so there the skill can load like any other. It still
    refuses to run without a key, and it still shows you the job before it sends
    one.

## Your key, and where it goes

You need an Edison API key. It lives in one file on your own machine,
`~/.claude/compute/edison.env`:

```bash
mkdir -p ~/.claude/compute
printf 'export EDISON_PLATFORM_API_KEY=PASTE-YOUR-EDISON-KEY-HERE\n' \
  > ~/.claude/compute/edison.env
chmod 600 ~/.claude/compute/edison.env
```

Then open the file in your editor and paste your key over the placeholder. You do
not have to remember any of this: when something is missing, the check the skill
runs first prints those exact commands back to you.
[`templates/edison.env`](https://github.com/liuhlab/liulab-compute-skills/blob/main/templates/edison.env)
is the same file with the reasoning in its comments. The variable name is the one
the client reads and no other, and the `chmod` leaves the file readable by you
alone.

The key sits beside `personal.md`, never inside it. An agent reads `personal.md`
into the chat, so a key written there would be copied into every transcript you
ever record.

Before it does anything, the skill checks that file. If it is missing, still holds
the placeholder, or is readable by other people, the agent stops and says which
check failed. It offers to write the file for you, with the placeholder in place,
and then hands it back to you. It will never ask you to type or paste your key
into the chat.

## What happens before it spends

You see the job and the query. The skill names the job it picked and prints your
question in full, before the task goes out.

The costly runs stop and ask: a deep literature run, a data analysis run, and any
batch of more than three tasks. A follow-up rides on the run you just read,
instead of paying again for the same background.

No prices appear anywhere in this repo. They change, and a stale number is worse
than none at all. Check the balance on the platform when the cost matters.

## A run takes minutes, and the id is the receipt

Edison runs are slow enough that nobody should sit and watch one. The skill sends
the task, prints the task id straight away, and then checks on it. You get your
terminal back.

That id outlives the session that made it. If your laptop sleeps, the window
closes, or the agent stops early, the run carries on and finishes on the platform.
So a run is never really lost: the skill can list the tasks on your account,
newest first, and find the one you started. It offers to do that before asking the
same question twice, because asking twice means paying twice for an answer you
already own. It can also cancel a run you started by mistake, which is worth
knowing before a long data analysis job.

## Kosmos, for a goal rather than a question

Kosmos is the platform's heavyweight agent, and the reason to come here when what
you have is bigger than one query. It is not a task you send off. You pick a
persona, make a project inside it, and talk to it there. Kosmos splits your goal
into many smaller tasks and works through them in rounds until it decides it is
done. One real project ran thirteen of them.

That shape is also what makes it cost. A run pays for every task it fans out to,
so there is no flat price to quote, and the skill will not start one unless you
ask for that run in plain words.

Everything it does around a run is free. It drafts the goal with you, checks your
data is in a shape Kosmos can use, and shows you a run you already started, task
by task, without opening a browser.

## One question, one job

For a single question the skill picks one of the platform's one-shot jobs and
routes to it.

| You are asking | What it picks |
| --- | --- |
| A question the published papers can answer, with citations | The literature job |
| The same, but the papers disagree and it needs real reasoning | The deeper literature job, slower and dearer |
| Has anyone done this before? | The precedent job |
| Chemistry: molecules, properties, how to make one | The molecules job |
| Something about a dataset you supply | The analysis job |

Ask in plain words and the skill picks for you. Say which one you want and it uses
that.

## Where your data sits

Your own machine, by default, because that is where your key belongs. Data on
your laptop uploads and runs with nothing to arrange. Data on a cluster comes down
first and uploads from here, so your key stays off shared hardware. You can run
Edison on arc, but only after you put the key there yourself, in your own session.
The skill never copies your key anywhere: not to a cluster, not into a job script,
not onto a command line.

## The first run is slow

The client is never installed into anything you maintain. It runs from a throwaway
environment, so it cannot break your pixi setup, and an active pixi shell does not
disturb it.

The cost is the first run on a new machine. Dozens of packages download before your
question is even sent, and it can look hung for a minute or two. It is not. Every
later run reads from the cache and starts at once.
