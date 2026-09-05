"""The preflight: the constants contract, the parsing, and the dependency it must not have.

`tests/lint.sh` owns the six behavioural verdicts, because there it doubles as the fixture
builder for the no-secrets sweep. What is here is what a shell test cannot say well: that the
module runs on a machine where nothing at all is installed, and that it reads a key file the
way sourcing it would.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from edison_cli import preflight

REPO = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO / "src" / "edison_cli" / "preflight.py"
CONSTANT_NAMES = ("VAR", "PLACEHOLDER", "KEYFILE", "MODE_GLOB", "MODE_LABEL", "CHMOD_MODE")


def test_constants_are_key_equals_value_lines_and_nothing_else() -> None:
    """The shape is the contract: `tests/lint.sh` parses this with `sed`."""
    lines = preflight.constants()
    assert [line.split("=", 1)[0] for line in lines] == list(CONSTANT_NAMES)
    for line in lines:
        name, _, value = line.partition("=")
        assert value, f"{name} printed no value"
        assert name.isupper()


def test_the_key_file_constant_follows_the_override() -> None:
    """`-f` has to move the reported file, or the gate would build fixtures for another path."""
    reported = dict(line.split("=", 1) for line in preflight.constants("/tmp/somewhere.env"))
    assert reported["KEYFILE"] == "/tmp/somewhere.env"
    assert reported["VAR"] == preflight.VAR


def test_the_remedy_hands_out_a_mode_the_check_accepts() -> None:
    """A remedy the preflight's own permission test rejects would loop a user forever."""
    import fnmatch

    assert fnmatch.fnmatch(preflight.CHMOD_MODE, preflight.MODE_GLOB)


def test_the_preflight_runs_with_neither_the_client_nor_typer_installed(tmp_path: Path) -> None:
    """The no-secrets sweep is a security control and must not depend on a hundred packages.

    Proved rather than asserted in a comment: `edison_client` and `typer` are replaced with
    packages that raise on import and put first on the path, so importing either one is a
    failed test rather than a passing one.
    """
    poison = tmp_path / "poison"
    for name in ("edison_client", "typer", "click", "rich"):
        package = poison / name
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            f'raise ImportError("the preflight must not import {name}")\n', encoding="utf-8"
        )
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "PYTHONPATH": str(poison),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    done = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--constants"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    printed = [line.split("=", 1)[0] for line in done.stdout.splitlines()]
    assert printed == list(CONSTANT_NAMES)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("export {var}=plain\n", "plain"),
        ("{var}=no-export-word\n", "no-export-word"),
        ('export {var}="double quoted"\n', "double quoted"),
        ("export {var}='single quoted'\n", "single quoted"),
        ("   export   {var}=indented\n", "indented"),
        ("export {var}=first\nexport {var}=last\n", "last"),
        ("# a comment\nexport OTHER=x\n", ""),
    ],
)
def test_a_key_file_is_read_the_way_the_shell_would_read_it(
    tmp_path: Path, body: str, expected: str
) -> None:
    """The file used to be sourced by bash. Reading it differently would change who is configured."""
    key_file = tmp_path / "key.env"
    key_file.write_text(body.format(var=preflight.VAR), encoding="utf-8")
    key_file.chmod(0o600)
    report = preflight.check(str(key_file))
    assert report.secret == expected
    assert report.ok is bool(expected)


def test_the_report_never_carries_the_key_into_its_repr(tmp_path: Path) -> None:
    """Whatever this package prints lands in a transcript, and a `repr` is printed by accident."""
    key_file = tmp_path / "key.env"
    key_file.write_text(
        f"export {preflight.VAR}=a-value-that-must-not-be-repeated\n", encoding="utf-8"
    )
    key_file.chmod(0o600)
    report = preflight.check(str(key_file))
    assert report.ok
    assert "a-value-that-must-not-be-repeated" not in repr(report)
    assert "a-value-that-must-not-be-repeated" not in report.text()
