---
search:
  exclude: true
---

# Edison is one skill, inside the plugin the lab already installs

`lab-edison` is a single skill under `skills/`, in the existing `lab-compute` plugin. Not
several skills, not a plugin of its own, and no bundled MCP server. It is the first skill
here that never touches a cluster.

## Why one skill and not several

The platform exposes five jobs, and each could plausibly be its own recipe — ADR 0002 says
a repeatable procedure gets its own skill. That reading fails here, because the trigger
vocabulary is one overlapping cloud: every request says "Edison" and then something about
literature, precedent, chemistry or a dataset. Five descriptions matching the same words
turn the choice between them into a coin toss.

Three things are also shared by every path — the key check, the rule that spend is shown
before it is spent, and the routing table saying which job answers which question. Split
the skill and all three are copied five times, where they drift apart quietly and the copy
that drifted is the one an agent happens to load. Per-job detail goes to `references/`
instead, which is the other half of ADR 0002.

## Why the existing plugin and not a new one

ADR 0001 already decided that one plugin holds every skill, and nothing about a cloud API
argues otherwise. A second plugin buys someone the ability to install Edison without the
HPC skills — which are Markdown, and which the same people install anyway. It costs every
lab member a second marketplace to add and a second version number to keep current.

## Why no bundled MCP server

The vendor ships an official MCP server, and a plugin can configure one. That would charge
every lab member who installed an HPC plugin an always-on tool budget in their context and
an external process on their machine, whether or not they ever use Edison. The ephemeral
client invocation costs nothing until someone asks for it.

## What it costs

The plugin's description has to widen past "HPC clusters and remote-compute workflow" to
admit a skill with no cluster in it, and `lab-compute` becomes a slightly loose name for
what the plugin holds. Reversal is a new plugin name that every installed machine has to
add by hand, which is why this is written down.
