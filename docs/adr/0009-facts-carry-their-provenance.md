---
search:
  exclude: true
---

# Facts carry their provenance, at one of three tiers

Every `lab-edison` reference page opens with a provenance block: the page's default source,
the date it was checked, and the tier that holds unless a claim says otherwise. Three tiers,
and only three — **verified** (we ran it and saw the result), **read** (from the package
source or a vendor page, not run), **unverified** (inferred or assumed). A claim at another
tier is tagged where it is made. `tests/lint.sh` fails a page with no block, and a block
whose date will not parse.

## Why dating cluster facts was not enough

The re-verify rule was written for clusters, where checking again is a read-only command on
a compute node and costs nothing. A vendor's platform has neither property: it changes under
us without notice, and several of its facts can only be observed by spending a credit. So the
skill shipped three factual errors in four releases: Kosmos called browser-only, reasoned
from a package that never mentions it; a wrong vendor; a cost repeated six times from no
source. Each was caught by a person, because a claim arrived as prose saying nothing about
where it came from, and no rule in the gate read a date.

## Why three tiers

They separate the three things an agent may tell a user: we ran this, we read this, we
guessed. Two tiers would fold reading into one of the neighbours — dishonest against
verified, useless against unverified, and honest reading of the package is most of what these
pages are. More would grade confidence — a judgement, not a fact about how the claim
was obtained.

## The two granularities rejected

**A tag on every claim.** Truthful and unreadable: these pages are word-capped, and marking
every sentence buries the handful of exceptions. A default plus tagged exceptions carries the
same information and makes the exception the thing you see.

**Package versus vendor page as tiers of their own.** The skill already ranks those two —
believe the package over any vendor page — so a second encoding lets the tier and the Source
line contradict each other with nothing to catch it. The Source line says where; the tier
says how.

## What it costs

The gate cannot tell whether a date is honest, and nothing can: a block that is never
re-checked keeps reading as current. Only `lab-edison` carries blocks today. Extending it is
four more lines and one wider glob; undoing it is deleting one check.
