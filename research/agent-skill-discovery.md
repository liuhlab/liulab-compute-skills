# How Claude Code, Codex and Kimi Code find, namespace and update skills

Research for #63 (map #62), 2026-10-10. Versions examined:

- Claude Code 2.1.296, against the official docs.
- codex-cli 0.162.1, source tag `rust-v0.162.1` = `092d3ac`.
- Kimi Code 2.1.1, source tag `@moonshot-ai/kimi-code@2.1.1` = `f67e639`. The source is public under MIT.
- vercel-labs/skills (`npx skills`) 1.7.2, read at main `13e4063`, whose only change since the release is an unrelated agent entry.

Tiers: **verified** means run or inspected on a lab machine. **read** means docs or source, not run. **unverified** means inferred.

Citation prefixes:

- `CC/` = `https://code.claude.com/docs/en/`
- `CX/` = `https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/`
- `KM/` = `https://github.com/MoonshotAI/kimi-code/blob/f67e6398fb3210ad8ace970e2dfd5bcc984ed61f/`
- `KS/` = `KM/packages/agent-core-v2/src/`
- `VS/` = `https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/`

## Answer

- **No one mechanism reaches all three.** Claude Code and Codex both install this repo as a plugin marketplace, from the `.claude-plugin/` files it already has. Codex reads `.claude-plugin/marketplace.json` as a fallback. Kimi Code reads neither format.
- **Both plugin routes can update themselves from a public GitHub repo, with no token.**
  - Codex does it by default at startup: `git ls-remote`, then on a new revision a re-clone and reinstall.
  - Claude Code does it only once auto-update is on for the marketplace. It is off by default for third-party marketplaces. Each user turns it on with the `/plugin` toggle, or with `"autoUpdate": true` on an `extraKnownMarketplaces` entry in a settings file.
  - **ADR 0004's premise is wrong.** It says auto-update "needs a `GITHUB_TOKEN` on every machine". The token was only ever for private repos, and the docs now say an env token alone does not authenticate the check even there.
- **Kimi Code reads loose skill directories live from disk.** These are `~/.kimi-code/skills`, `~/.agents/skills`, the repo's `.kimi-code/skills` and `.agents/skills`, and any `extra_skill_dirs` listed in `config.toml`. Its plugins use a Kimi-only manifest (`.kimi-plugin/plugin.json`) and update only by manual reinstall. So for Kimi, the path that needs no reinstall is a git checkout it reads directly, kept current by `git pull`.
- **`~/.agents/skills` is the one directory Codex and Kimi share.** Claude Code's docs don't list it. Lab skills placed there load a second time in a Codex that also has the plugin. Codex keeps both copies, and where the two end up with the same name, a bare `$name` picks neither. Kimi's `extra_skill_dirs` reaches Kimi alone.
- **A repo's own skills layer on top in all three.** Claude Code and Codex namespace plugin skills (`/lab:lab-hpc`, `$lab:lab-hpc`), so a repo skill with the same short name loads beside them. Kimi does not namespace: a project skill silently replaces a lab skill of the same name.
- **`npx skills` is a poor fit for the lab set.**
  - It copies only `skills/<name>/`: no `bin/`, no `src/edison_cli`.
  - It updates only when someone runs it.
  - It never picks up a skill added after the first install.
  - It sends telemetry by default.
- **The user-only gate and `bin/` differ by agent.**
  - Claude Code and Kimi both honour `disable-model-invocation: true`.
  - Codex ignores that key. It needs `agents/openai.yaml` with `policy.allow_implicit_invocation: false`.
  - Only Claude Code puts a plugin's `bin/` on PATH, so a bare `edison-cli` fails in Codex and Kimi.

## Comparison

Tier per cell: [v] verified, [r] read, [u] unverified. The evidence below gives the source for each.

| | Claude Code | Codex | Kimi Code |
| --- | --- | --- | --- |
| User skill dirs | `~/.claude/skills` [r] | `~/.agents/skills`; `$CODEX_HOME/skills` (deprecated); `/etc/codex/skills` [r] | `~/.kimi-code/skills`, then `~/.agents/skills`; `extra_skill_dirs` [r] |
| Repo skill dirs | `.claude/skills` from cwd up to repo root; nested dirs on demand [r] | `.agents/skills` from repo root down to cwd; `.codex/skills` [r] | `.kimi-code/skills`, `.agents/skills` at the git root only [r] |
| Reads `~/.agents/skills` | Not in the docs' location table [r]; reachable through a `~/.claude/skills` symlink [v] | Yes [r] | Yes [r] |
| Same short name twice | Enterprise > personal > project [r] | Both kept; bare `$name` selects neither [r] | Project > user > extra > plugin > built-in, silently [r] |
| Marketplace from GitHub | `claude plugin marketplace add owner/repo` [r] | `codex plugin marketplace add owner/repo` [v] | Own catalog format only; TUI `/plugins install <github url>` installs one plugin [r] |
| Reads `.claude-plugin/` | Native [r] | As a fallback [r]; lists `lab@liulab` [v] | No; `.kimi-plugin/plugin.json` or `kimi.plugin.json` [r] |
| Plugin skill name | `/lab:lab-hpc` [v] | `lab:lab-hpc`, mentioned `$lab:lab-hpc` [r] | `/skill:lab-hpc`, no namespace [r] |
| Update | Auto if turned on; else `claude plugin update lab@liulab` [r] | Auto at startup, on by default; `codex plugin marketplace upgrade` [r] | Plugins: reinstall by hand. Loose dirs: read live [r] |
| Auto-update needs | Toggle or settings `autoUpdate`; git; no token for a public repo [r] | git and network; no token for a public repo [r] | — |
| What triggers a new copy | Computed version changes; `plugin.json` `version` first [r] | New marketplace revision; cache dir named by `version` [r] | Reinstall [r] |
| Follows a symlinked skill dir | Yes [v] | Yes, except the system root [r] | Yes [r] |
| Symlinks inside an installed plugin | Kept if inside the plugin [r][v] | Dropped [r][v] | Zip installs write regular files [r] |
| User-only skill | `disable-model-invocation: true` [r][v] | `agents/openai.yaml` `allow_implicit_invocation: false` [r] | `disable-model-invocation: true` or `type: flow` [r] |
| Plugin `bin/` on PATH | Yes [r][v] | No [r] | No [r] |
| Description cut in listing | 1536 chars [r] | 1024 chars [r] | 250 chars [r] |
| `npx skills` writes | `~/.claude/skills/<n>` symlink to `~/.agents/skills/<n>` [r][v] | `~/.agents/skills` [r] | `~/.agents/skills` [r] |

## What this means for #71 (install path) and #68 (naming)

The four candidates from #71, against the evidence:

1. **A plugin marketplace per agent.** One repo serves Claude Code and Codex unchanged. Both namespace as `lab:`, both auto-update without a token, and both can be set once per machine. Kimi needs an added `.kimi-plugin/plugin.json`; obra/superpowers ships all three manifests side by side. Kimi then reinstalls by hand, with no update prompt for a plugin outside Kimi's own marketplace, and gets no `bin/`.
2. **One clone linked into each agent's skill dir.** `git pull` updates all three, and a scheduled pull makes that automatic. The cost: Claude Code loses `/lab:` and `bin/` on PATH, and must not also have the plugin, or every skill loads twice. In Codex a symlink into a checkout that carries `.claude-plugin/plugin.json` may still get the `lab:` prefix, which duplicates the plugin's name [u].
3. **`npx skills` at this repo.** It reaches all three through `~/.agents/skills` and a Claude Code symlink. It drops `bin/` and `src/`, updates by hand, misses new skills, and names skills bare.
4. **A hybrid.** The plugin for Claude Code and Codex, plus a checkout named in Kimi's `extra_skill_dirs` and kept current by `git pull`. Codex never reads that key, so nothing loads twice.

For #68: plugin skills are namespaced in Claude Code and Codex but not in Kimi. In Kimi a user or project skill of the same name (an `npx skills` copy of `tdd`, say) shadows the lab plugin's. Claude Code also answers a bare `/tdd` for `lab:tdd` unless another command owns that name. In Codex two enabled skills with the same full name make a bare mention select neither.

## Evidence: Claude Code

- **Skill locations [read].** `CC/skills#where-skills-live` lists enterprise, personal `~/.claude/skills`, project `.claude/skills`, nested, `--add-dir`, plugin and claude.ai. Project skills load "in the directory where you start it and in every parent directory up to the repository root".
  - No `.agents` skill path appears anywhere in the docs. `CC/memory#agents-md` says anything under `.agents/` is "Not read", but that line is about instruction files.
  - Whether Claude Code reads `~/.agents/skills` without a symlink is **unverified**.
- **Precedence [read].** `CC/skills#resolve-skills-that-share-a-name`: "Enterprise over personal, and personal over project". For a plugin skill against any other: "Both load, because plugin skills are namespaced as `/plugin-name:skill-name`".
  - "The bare `/fancy` also invokes the skill unless another command already uses that name."
  - **Verified:** this session lists `lab:lab-hpc`, `lab:lab-containers` and `lab:lab-jupyter`.
- **Marketplace [read].** The catalog lives at `.claude-plugin/marketplace.json`; `"."` or `"./"` means the repo root. `plugin.json` is optional (`CC/plugins/marketplace-reference`, `CC/plugins/manifest-reference`).
  - For `owner/repo`, Claude Code probes SSH and falls back to HTTPS; `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` skips the probe.
  - **Verified:** the installed `lab` cache holds the whole repo tree, so `source: "./"` ships everything.
- **Auto-update [read].**
  - `CC/plugins/install`: auto-update is "Off by default: every other marketplace, including … third-party marketplaces".
  - `CC/plugins/host-marketplace#turn-on-auto-update`: "`marketplace.json` has no field to turn it on". A user flips **Enable auto-update** under `/plugin`.
  - `CC/plugins/loading#when-auto-update-runs`: the first setting found decides, starting with "`autoUpdate` on its `extraKnownMarketplaces` entry in a settings file".
  - Timing (same page): "after you send your first message, Claude Code waits a random delay of up to ten minutes". The new copy loads at the next launch.
  - Off when `DISABLE_AUTOUPDATER`, `DISABLE_UPDATES` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set, unless `FORCE_AUTOUPDATE_PLUGINS=1`.
  - **Verified:** no `known_marketplaces.json` entry here carries `autoUpdate`.
- **Token [read].** `CC/plugins/host-marketplace#what-background-auto-update-does-with-credentials` is about private marketplaces only. "If a user sets `GITHUB_TOKEN` … that alone doesn't authenticate the background check. A token takes effect through a credential helper".
  - A 2026-03 archived copy of the old page said private marketplaces needed `GITHUB_TOKEN`/`GH_TOKEN`. This is likely where ADR 0004's claim came from [unverified].
  - The changelog for 2.1.280 fixed auto-update "ignoring git credential helpers". A public repo needs neither a token nor a helper.
- **Versions [read].** `CC/plugins/loading#how-claude-code-computes-the-version`: the order is manifest `version`, then the entry's `version`, then for a relative path "The commit SHA of the installed directory". A pinned `version` "keeps every user on the cached copy until its author changes the string". "The version also names the plugin's cache directory."
  - **Verified:** the cache directory is the `plugin.json` version.
  - **Read:** `claude plugin marketplace update` with no name "refreshes every marketplace's listing but leaves your installed plugins at their current versions". `claude plugin update <p>@<m>` installs the new copy.
  - AGENTS.md release step 4 names only the first command. Whether the named form (`… update liulab`) also moves the plugin is **unverified**.
- **Symlinks.**
  - **Read:** an entry in a personal or project location "can be a symlink to a directory elsewhere on disk" (`CC/skills`).
  - **Read:** inside a plugin, a symlink within the plugin "is preserved as a relative symlink in the cache". One pointing elsewhere in the marketplace is dereferenced, and one outside it is skipped (`CC/plugins/host-marketplace#share-files-within-a-marketplace-with-symlinks`).
  - **Verified:** this session loads `research` from `~/.claude/skills/research`, a relative symlink into `~/.agents/skills`. The repo's `CLAUDE.md -> AGENTS.md` is still a symlink in the plugin cache.
- **User-only [read].** `disable-model-invocation: true`: "Description not in context, full skill loads when invoked"; "If Claude tries anyway, Claude Code blocks the call" (`CC/skills`).
  - **Verified:** exactly the 13 linked skills that set the key are missing from this session's model-visible list, and so is `lab-edison`.
- **`bin/` [read].** `CC/plugins/components#executables`: "Files in `bin/` at the plugin root are on the `PATH` of the Bash tool's shell while the plugin is enabled". The entries come after the user's PATH. "claude.ai and Cowork don't install a plugin that has a top-level `bin/` directory."
  - **Verified:** `edison-cli` resolves in this shell.
- **Description cap [read].** The listing truncates at 1,536 characters (`CC/skills`).

## Evidence: Codex

- **Skill roots [read].** `CX/ext/skills/src/host_roots.rs#L48-131` collects, in this order:
  - user `$CODEX_HOME/skills` (commented "Deprecated … kept for backward compatibility"), then `~/.agents/skills`, then the bundled `$CODEX_HOME/skills/.system`;
  - admin `/etc/codex/skills`;
  - repo `.codex/skills` from project config folders;
  - plugin roots;
  - repo `.agents/skills` in each directory from the project root (nearest `.git`) down to cwd.
  - The skills docs (developers.openai.com/codex/skills) list REPO, USER, ADMIN and SYSTEM the same way.
  - The scan goes 6 levels deep, skips hidden directories, and the frontmatter read is `name`, `description` and `metadata.short-description` (`CX/ext/skills/src/loader/mod.rs#L19-32`, `CX/skills/src/parser.rs`).
- **Same name [read].** Skills are de-duplicated by path, never by name (`CX/ext/skills/src/loader/host_merge.rs#L228-267`). A bare `$name` selects a skill only when exactly one enabled skill has that name (`CX/skills/src/selection.rs#L33-39`). The docs: Codex "doesn't merge them; both can appear in skill selectors."
- **Marketplace format [read, verified].** `MARKETPLACE_MANIFEST_RELATIVE_PATHS` tries `.agents/plugins/marketplace.json`, `.agents/plugins/api_marketplace.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, and uses the first found (`CX/core-plugins/src/marketplace.rs#L20-25`).
  - The plugin manifest search is: a root `plugin.json` with an agent-plugins `$schema`, then `.codex-plugin/plugin.json`, then `.claude-plugin/plugin.json` (`CX/utils/plugins/src/plugin_namespace.rs#L46-87`).
  - `source: "./"` means the marketplace root (`marketplace.rs#L677-720`). With no `skills` field, `skills/` is scanned (`CX/core-plugins/src/loader.rs#L1082-1110`).
  - **Verified:** `codex plugin list` reads `~/.codex/.tmp/marketplaces/liulab/.claude-plugin/marketplace.json` and lists `lab@liulab`.
  - So adding `.agents/plugins/marketplace.json` or `.codex-plugin/plugin.json` would *replace* what Codex reads, and leave two manifests to keep in step.
- **Config and cache [verified, read].** `~/.codex/config.toml` holds `[marketplaces.liulab]` with `source_type = "git"`, `source`, and optional `ref` and `sparse_paths`. Installed plugins appear as `[plugins."<plugin>@<marketplace>"] enabled = true` (`CX/config/src/types.rs#L1102-1122`).
  - The cache path is `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`, with the version from `plugin.json` or `local` if absent (`CX/core-plugins/src/store.rs#L112-120`).
  - `copy_dir_recursive` copies only regular files and directories, so symlinks are dropped (`store.rs#L736-760`). **Verified:** the cached copy has `AGENTS.md` but no `CLAUDE.md`.
- **Namespace [read].** Plugin skills are named `<plugin.json name>:<skill>` (`CX/ext/skills/src/loader/namespace.rs#L11-24`). `:` is legal in a `$` mention (`CX/skills/src/mentions.rs`).
  - A symlink in `~/.agents/skills` pointing into a checkout that carries `.claude-plugin/plugin.json` may also be named `lab:…`, because namespace lookup walks up from symlink targets. This is **unverified**: the tests cover only the reverse case (`namespace_tests.rs#L117-173`).
- **Updates [read, verified].** At app-server startup, which the TUI runs in-process, Codex auto-upgrades configured git marketplaces: `git ls-remote`, a fresh clone if the revision changed, then a forced reinstall of configured plugins (`CX/core-plugins/src/marketplace_upgrade.rs#L225-298`, `CX/app-server/src/in_process.rs#L517`).
  - git runs with `GIT_TERMINAL_PROMPT=0` (`CX/core-plugins/src/marketplace_upgrade/git.rs#L157`). No token is involved, and a public repo needs none.
  - The manual form is `codex plugin marketplace upgrade [NAME]` [verified, `--help`].
  - **A renamed plugin is never migrated.** The reinstall skips it with "configured non-curated plugin no longer exists" (`loader.rs#L658`).
  - **Verified:** on one lab machine the marketplace snapshot records the current main revision. Yet `lab-compute@liulab` stays installed at `2026.9.16`, and `lab@liulab` shows "not installed".
- **Symlinks [read].** Directory symlinks are followed in user, repo, admin and plugin roots, but not in the system root. A symlinked `SKILL.md` file is ignored (`CX/ext/skills/src/loader/host.rs#L164-167`; test `follows_directory_symlinks_except_for_system_scope`). The docs say Codex "supports symlinked skill folders".
- **User-only [read].** `<skill>/agents/openai.yaml` with `policy.allow_implicit_invocation: false` hides a skill from the model; it defaults to true (`CX/ext/skills/src/loader/metadata.rs#L27-56`). An explicit mention still works.
  - `disable-model-invocation` appears nowhere in the source, and unknown frontmatter keys are accepted silently.
  - **Verified:** the installed mattpocock skills pair `disable-model-invocation: true` with exactly this `openai.yaml`.
- **Other components [read].**
  - `bin/` is not put on PATH; the only PATH prepends are Codex's own (`CX/core/src/tools/runtimes/mod.rs#L127-152`).
  - Hooks run only after the user trusts them, and only hooks get `CLAUDE_PLUGIN_ROOT`.
  - `.mcp.json` is read, and `commands/*.md` become skills at install.
  - The manifest parser reads `name`, `version`, `description`, `keywords`, `skills`, `mcpServers`, `apps`, `hooks` and `interface` (`CX/core-plugins/src/manifest.rs#L48-73`).
- **Description cap [read].** `MAX_CATALOG_SKILL_DESCRIPTION_CHARS = 1_024` (`CX/ext/skills/src/render.rs#L23`). A description of 1025 to 1536 characters passes this repo's lint but is cut in Codex. Today's are all under 700.
- **Per-skill switch [read].** `[[skills.config]]` with `name = "lab:lab-edison"` or `path = …` and `enabled = false`, in the user `config.toml` only (`CX/config/src/skills_config.rs`).

## Evidence: Kimi Code

- **Source [read].** `MoonshotAI/kimi-code` is the 2.x TypeScript agent; `MoonshotAI/kimi-cli` is the archived Python predecessor. **Verified:** the installed binary's strings carry the `agent-core-v2` constants quoted below.
- **Skill roots [read, verified].** `KS/features/skill/catalog/skillRoots.ts#L8-37`:
  - user: `$KIMI_CODE_HOME/skills` (default `~/.kimi-code/skills`), then `~/.agents/skills`, always under the OS home;
  - project: `.kimi-code/skills`, then `.agents/skills`, at the nearest ancestor containing `.git`;
  - `extra_skill_dirs` in `config.toml`, where missing directories are skipped silently.
  - Nothing reads `~/.claude/skills` or `~/.codex/skills`. A built-in `/import-from-cc-codex` makes a one-time copy and skips plugins.
  - `--skills-dir` replaces only the user and project tiers [verified, `kimi --help`].
- **Precedence [read].** `SKILL_SOURCE_PRIORITY`: builtin 0, plugin 5, extra 10, user 20, workspace 30. The higher tier replaces the lower silently, and names compare case-insensitively (`KS/features/skill/catalog/skillSource.ts#L11-17`). The docs leave out the plugin tier.
- **Plugins [read].**
  - **Manifest:** `kimi.plugin.json` or `.kimi-plugin/plugin.json` (`KS/app/plugin/manifest.ts#L16-17`). There is no `.claude-plugin` or `.codex-plugin` reader.
  - **Install:** from GitHub, `/plugins install https://github.com/<o>/<r>[/tree/<ref>]` in the TUI. `kimi --help` has no plugin subcommand [verified].
  - **Which commit:** a bare repo URL installs "the latest release; falls back to the default branch if no release exists" (`KM/docs/en/customization/plugins.md#L47`). This repo tags but publishes no Releases, so Kimi would install `main` HEAD.
  - **Scope:** per user only; project scope is "not yet supported" (`plugins.md#L59`).
  - **Marketplace:** Kimi's own JSON (`{"version":"2","plugins":[{"id",…}]}`). One URL replaces the default (`KIMI_CODE_PLUGIN_MARKETPLACE_URL`), and a Claude `marketplace.json` fails to parse (`KS/app/plugin/marketplace.ts`).
  - **Precedent:** obra/superpowers ships `.kimi-plugin/plugin.json` = `"skills": "./skills/"` beside its Claude and Codex manifests.
- **Namespace [read].** Users invoke `/skill:<name>`, and a bare `/<name>` also resolves. The model uses a `Skill` tool. Plugin skills register under the bare name; only plugin *commands* get a `<plugin>:` prefix (docs `plugins.md`; `KS/features/skill/catalog/registry.ts`).
- **Updates [read].** "Official plugins do not update automatically … repeat the installation steps" (`plugins.md#L98`). Skill directories are read from disk, with file watchers on by default since 2.1.1. A checkout reached through `~/.agents/skills` or `extra_skill_dirs` is therefore updated by `git pull`.
- **Symlinks [read].** Discovery uses `stat` and `realpath`, so symlinked roots and per-skill links are followed (`skillRoots.ts`, `fileSkillDiscovery.ts`). Zip installs write plain files.
  - Since 2.1.0, file tools refuse paths that escape through symlinks. Skill roots are allowed by realpath, so reading a linked skill's `references/` may still prompt or fail — **unverified**.
- **User-only [read, verified].** `METADATA_ALIASES` maps `disable-model-invocation` and `disable_model_invocation` to `disableModelInvocation` (`KS/features/skill/catalog/parser.ts#L48-49`). Such skills are hidden from the listing, and the tool refuses them. Kimi's own form is `type: flow`.
  - So the claim in this repo's `CONTEXT.md` and README that other tools ignore the key is wrong for Kimi.
- **Scripts [read].** There is no plugin `bin/` on PATH. Skills reference bundled files as `${KIMI_SKILL_DIR}/…`, and `${CLAUDE_PLUGIN_ROOT}` is not expanded.
- **Description cap [read, verified].** `LISTING_DESC_MAX = 250` (`KS/features/skill/catalog/registry.ts#L12`). Every lab description is longer, so Kimi triggers on a truncated description unless a Kimi `whenToUse` field adds a full line.
- **Local note [verified].** A stale `extra_skill_dirs` entry from before the repo rename loads nothing, silently.

## Evidence: `npx skills` (vercel-labs/skills)

- **Targets [read, verified].** `VS/src/agents.ts`:
  - `claude-code` writes `~/.claude/skills`, or `.claude/skills` in a project.
  - `codex` writes `~/.agents/skills` (`#L224-232`).
  - `kimi-code-cli` writes `~/.agents/skills` (`#L462-470`), detected by `~/.kimi-code` or `~/.kimi`.
  - Agents whose dir is `.agents/skills` share the one canonical copy; every other agent gets a relative symlink to it (`VS/src/installer.ts#L405-415`).
  - **Verified:** the `~/.claude/skills` entries here are `../../.agents/skills/<name>` links.
- **What it copies [read].** It copies the skill folder only, including `agents/openai.yaml`, `scripts/` and `references/`. It never installs a Claude or Codex plugin.
  - It finds skills in a Claude plugin repo through `.claude-plugin/marketplace.json`, or by scanning `skills/` (`VS/src/plugin-manifest.ts#L51-112`).
  - It reads only `name`, `description` and `metadata.internal` from frontmatter, and names skills bare.
- **Lock and updates [read].** `~/.agents/.skill-lock.json` (schema v3) records each skill's `source`, `skillPath` and `skillFolderHash`, which is the GitHub tree SHA of the folder (`VS/src/skill-lock.ts#L13-60`).
  - `skills update` (`check` is an alias and also installs) makes one anonymous Trees API call per source. It falls back to `GITHUB_TOKEN`/`GH_TOKEN`, then `gh`, then `git clone`, so no token is required (`VS/src/update.ts#L496-662`).
  - It never runs by itself, and it updates only names already locked, so new skills need a fresh `add`.
  - Telemetry to skills.sh is on unless `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` (`VS/src/telemetry.ts`).

## Corrections this research implies

- **ADR 0004:** the `GITHUB_TOKEN` premise is wrong for a public repo. Auto-update is a per-user switch, or a settings key, with no token.
- **AGENTS.md release step 4:** `claude plugin marketplace update liulab` may refresh only the listing. The docs give `claude plugin update lab@liulab` as the command that moves the installed copy.
- **`CONTEXT.md`, README and `docs/skills/lab-edison.md`:** Kimi honours `disable-model-invocation`, so the gate already holds there. Codex needs `skills/lab-edison/agents/openai.yaml`.
- **`bin/edison-cli` comment:** other agents don't install by symlink. Codex copies and drops symlinks, and Kimi copies or unzips. The conclusion, no PATH entry, holds.

## Open questions only a session can settle

1. Does Claude Code read `~/.agents/skills` without a symlink? Add an unlinked probe skill there, start `claude`, run `/skills`, then remove the probe.
2. Does the named `claude plugin marketplace update liulab` move the installed plugin? After a version bump, run it and then `claude plugin list`.
3. Does token-free auto-update reach this public repo? Enable auto-update for `liulab`, push a bump, send one message, and wait up to ten minutes for "Plugin updated".
4. Does Codex name `lab-edison` `lab:lab-edison`, and does `openai.yaml` hide it? Install `lab@liulab`, then grep `codex debug prompt-input` for `lab:`. This makes no model call, but it starts a thread and runs hooks.
5. Does a symlink from `~/.agents/skills` into a checkout get Codex's `lab:` prefix? Use the same `codex debug prompt-input` check.
6. Does Kimi read a linked skill's `references/` without a path-escape refusal? Run `kimi -p "Use lab-hpc; print the first heading of references/arc-hpc.md" --output-format stream-json` with `lab-hpc` linked into `~/.agents/skills`.
7. Does Kimi still trigger `lab-hpc` on a 250-character description? Run `kimi -p "submit a tiny slurm job on arc" --output-format stream-json` and look for a `Skill` call.
