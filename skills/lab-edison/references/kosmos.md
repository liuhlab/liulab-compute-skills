# Kosmos

Companion to `SKILL.md`'s Kosmos section. Read it when a user asks for Kosmos — the whole
value this skill can add to a Kosmos run is spent before the run starts.

## Why there is nothing to submit

Read off the installed `edison-client` 0.16.1 on 2026-09-05:
`edison_client.models.app.JobNames` carries no Kosmos member. Literature, precedent,
molecules and analysis each have one; Kosmos has none, so there is no name to put in a
`TaskRequest` and nothing the client can send. The vendor's own tutorial for the package
uses only `JobNames.ANALYSIS` and never mentions Kosmos, and the agents page lists Kosmos
beside the other four while giving it no job name.

No vendor sentence is quoted here, on purpose: the current pages do not say Kosmos is
unavailable from the API in so many words, and a quotation that turns out not to exist is
worse than a check anyone can repeat. Repeat this one instead:

```bash
uv run --no-project --python 3.12 --with edison-client python -c \
  "from edison_client.models.app import JobNames; print([m.name for m in JobNames])"
```

If a later release lists a Kosmos member, believe the enum and fix this page.

## Briefing the run

The user starts the run themselves on the platform. What they type into it is the part you
can improve. Vendor guidance, from
<https://docs.edisonscientific.com/guides/best-practices-for-optimizing-kosmos-workflows>,
fetched 2026-09-05:

- **One well-defined objective**, with room for the run to generate hypotheses and test
  them as it goes. Not a list of separate questions.
- **Enough context to act on.** Phrase it as you would explain it to an experienced
  colleague who has just joined your team.
- **Not a fact lookup.** The answer should not be obvious after reading a few papers — a
  question like that belongs in `LITERATURE` and costs a fraction as much.

Draft it, show it, and let the user edit it before they paste it in.

## Preparing the dataset

Same source, same date:

- Processed data of good quality, not raw files.
- Every column name intuitively labelled. Where a name cannot carry its own meaning, add a
  sheet describing what each one means.
- It does best on complex, high-dimensional data.
- Under 5GB in total, uncompressed.

## Cost

A Kosmos run is roughly two orders of magnitude dearer than a single API agent task — the
difference between a question you ask in passing and one you decide to buy. Treat it as a
considered purchase: brief it properly, and check the dataset before the run rather than
after.

No figures here. The vendor's pricing page did not resolve on 2026-09-05, and the numbers
in circulation elsewhere are unconfirmed; a wrong price in a skill is worse than none.
Send the user to their platform balance for the current cost.

Nothing on this path calls the API, so the drafting and the dataset review spend no credits
of their own. The charge arrives only when the user starts the run in the browser.
