"""Preflight: whether this machine holds an Edison platform API key the client can read.

One verdict line per condition, and on failure the exact remedy. It NEVER prints the key or
any part of one — lengths and yes/no only, because whatever this writes lands in the agent's
transcript. The remedy lives here, not in SKILL.md, so a verdict and its fix cannot drift
apart and the agent relays tested text.

An exported key wins; otherwise the key file, default `~/.claude/compute/edison.env`. An
interactive shell rc is invisible here — agent tool calls run non-interactive shells — which
is why the file exists.

`-f` reads that file INSTEAD of the default and ignores the environment variable. The gate
drives this against fixtures, and on a maintainer's machine, where the real key IS exported,
every fixture would otherwise report configured and prove nothing.

This module is the ONE owner of the constants describing the key file: the variable name the
client reads, the shipped placeholder, the file's location, and which permission modes are
acceptable. `--constants` prints them and exits 0 without reading any key file, one
`KEY=value` per line, so the gate can assert that the onboarding template, the published page
and the no-secrets sweep still agree with these rather than each restating a literal. Nothing
there is secret: the placeholder is the shipped value, and a real key is never read, let
alone printed.

**It imports only the standard library, and it must stay that way.** `tests/lint.sh` reads
`--constants` inside the no-secrets sweep, which is a security control that has to keep
working with nothing installed, so it runs this file directly:

    python3 src/edison_cli/preflight.py --constants

That invocation has no package around it, which is also why nothing here is a relative
import. Exit: 0 configured, 1 not, 2 usage.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

VAR = "EDISON_PLATFORM_API_KEY"
PLACEHOLDER = "PASTE-YOUR-EDISON-KEY-HERE"
KEYFILE = Path.home() / ".claude" / "compute" / "edison.env"
# Owner-only is the rule; 600 is only the mode the remedy hands out. MODE_GLOB is what the
# check below actually applies, MODE_LABEL is the word prose should use for it, and
# CHMOD_MODE is what `chmod` is told. Saying "must be 600" anywhere is narrower than the
# check, and made four documents disagree with this file.
MODE_GLOB = "*00"
MODE_LABEL = "owner-only"
CHMOD_MODE = "600"

# The name is built into the pattern rather than written into it, so this line is not itself
# an assignment for the no-secrets sweep to flag. Last assignment wins, as when sourced.
_ASSIGNMENT = re.compile(rf"^[ \t]*(?:export[ \t]+)?{re.escape(VAR)}[ \t]*=[ \t]*(.*)$")


def display(path: Path) -> str:
    """Spell a path with `$HOME` collapsed to a tilde.

    An absolute home directory carries a username, and everything this file prints lands in
    a transcript.
    """
    home = str(Path.home())
    text = str(path)
    return f"~{text[len(home) :]}" if text.startswith(home + os.sep) else text


def constants(key_file: str | None = None) -> list[str]:
    """List the key-file constants as `KEY=value` lines and nothing else.

    `KEYFILE` reports the file the same invocation would check, so `-f` moves both the check
    and whatever reads this. Call it without `-f` to read the shipped location.
    """
    path = Path(key_file) if key_file else KEYFILE
    return [
        f"VAR={VAR}",
        f"PLACEHOLDER={PLACEHOLDER}",
        f"KEYFILE={display(path)}",
        f"MODE_GLOB={MODE_GLOB}",
        f"MODE_LABEL={MODE_LABEL}",
        f"CHMOD_MODE={CHMOD_MODE}",
    ]


@dataclass
class Report:
    """What the preflight found: the verdict lines, whether work may proceed, and the key.

    The key is carried in a field kept out of `repr` and out of comparison, and the only
    supported way to use it is `export`, which puts it where the client reads it. Nothing
    prints it, and no caller should reach for it.
    """

    lines: list[str]
    ok: bool
    secret: str = field(default="", repr=False, compare=False)

    def text(self) -> str:
        """Join the verdict lines into the report as a human reads it."""
        return "\n".join(self.lines)

    def export(self) -> None:
        """Put the key into this process's environment, which is the client's only route in."""
        os.environ[VAR] = self.secret


def _remedy(shown: str, reason: str) -> list[str]:
    """Spell out the failure and the exact commands that repair it.

    Nothing here is secret — the placeholder is the shipped value — and the fix is printed
    rather than performed, because the user pastes their own key.
    """
    parent = shown.rsplit("/", 1)[0]
    return [
        f"edison: NOT CONFIGURED ({reason})",
        "",
        "--- how to fix ---",
        f"mkdir -p {parent}",
        f"printf 'export {VAR}={PLACEHOLDER}\\n' > {shown}",
        f"chmod {CHMOD_MODE} {shown}",
        "",
        f"Then open {shown} in your own editor and replace {PLACEHOLDER} with the key from",
        "the Edison platform. Never paste a key into a chat, a command line, or a job script.",
        "",
        f"{VAR} is the only name edison-client reads; the vendor's README names a different",
        "one and is wrong. A key exported from an interactive shell rc is usually invisible to",
        "this check, because tool calls run non-interactive shells that never read one — the",
        "file fixes that.",
    ]


def _assigned_value(text: str) -> str:
    """Read the key out of a key file's text the way sourcing it would.

    The last assignment wins, and one layer of quotes comes off, because that is what the
    shell would do with the same file.
    """
    value = ""
    for line in text.splitlines():
        found = _ASSIGNMENT.match(line)
        if found:
            value = found.group(1)
    for quote in ('"', "'"):
        value = value.removesuffix(quote).removeprefix(quote)
    return value


def _mode(path: Path) -> str:
    """Report a file's permission bits the way `stat` and `chmod` spell them."""
    try:
        return format(path.stat().st_mode & 0o7777, "o")
    except OSError:
        return "?"


def check(key_file: str | None = None) -> Report:
    """Decide whether this machine is configured, and say why in full either way."""
    override = key_file is not None
    path = Path(key_file) if override else KEYFILE
    shown = display(path)
    lines: list[str] = []

    # 1. The environment. Tested for emptiness, never printed.
    if override:
        envnote = "the environment is ignored under -f"
    else:
        envnote = f"{VAR} is not exported here"
        exported = os.environ.get(VAR, "")
        if exported:
            lines.append(f"key: SET ({len(exported)} chars)")
            lines.append(f"edison: CONFIGURED (source: {VAR} exported into this process)")
            return Report(lines, True, exported)

    # 2. The key file, condition by condition.
    if not path.is_file():
        lines.append(f"key file: MISSING ({shown})")
        lines += _remedy(shown, f"no key file, and {envnote}")
        return Report(lines, False)
    lines.append(f"key file: PRESENT ({shown})")

    raw = path.read_bytes()
    if not raw:
        lines.append("key file: EMPTY (0 bytes)")
        lines += _remedy(shown, "key file is empty")
        return Report(lines, False)
    lines.append(f"key file: NON-EMPTY ({len(raw)} bytes)")

    value = _assigned_value(raw.decode("utf-8", "replace"))
    reasons: list[str] = []
    if not value:
        lines.append(
            f"key: NOT SET (the file assigns no {VAR} — the exact name edison-client reads)"
        )
        reasons.append(f"the key file assigns no {VAR}")
    elif value == PLACEHOLDER:
        lines.append("key: PLACEHOLDER (still the shipped value)")
        reasons.append("the placeholder was never replaced")
    else:
        lines.append(f"key: SET ({len(value)} chars)")

    # MODE_GLOB means the group and other bits are zero, so 600 and 400 both pass.
    mode = _mode(path)
    if fnmatch.fnmatch(mode, MODE_GLOB):
        lines.append(f"key file: PERMISSIONS {MODE_LABEL.upper()} (mode {mode})")
    else:
        lines.append(
            f"key file: PERMISSIONS TOO OPEN (mode {mode} — run: chmod {CHMOD_MODE} {shown})"
        )
        reasons.append(f"mode {mode} lets other people read it")

    if reasons:
        lines += _remedy(shown, "; ".join(reasons))
        return Report(lines, False)
    lines.append(f"edison: CONFIGURED (source: key file {shown})")
    return Report(lines, True, value)


def main(argv: list[str] | None = None) -> int:
    """Run the preflight from a command line, whether through `edison-cli` or on its own."""
    parser = argparse.ArgumentParser(
        prog="edison-cli preflight",
        description="Report whether this machine holds an Edison platform API key.",
    )
    parser.add_argument(
        "-f",
        "--key-file",
        metavar="FILE",
        help="check this file instead of the configured one, and ignore the environment",
    )
    parser.add_argument(
        "--constants",
        action="store_true",
        help="print the key-file constants as KEY=value lines and exit, reading no key file",
    )
    args = parser.parse_args(argv)
    if args.constants:
        print("\n".join(constants(args.key_file)))
        return 0
    report = check(args.key_file)
    print(report.text())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
