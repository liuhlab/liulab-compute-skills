"""The entry point, reachable both as `edison-cli` and as `python -m edison_cli`.

`[project.scripts]` names `edison_cli.__main__:main`, so `main` is re-exported here rather
than defined here: the parser and the dispatch live in `edison_cli.cli`, which is also what
the tests drive.
"""

from __future__ import annotations

from edison_cli.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
