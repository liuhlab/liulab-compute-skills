"""Makes `tests` a package, so a test module can import the harness as `tests.conftest`.

Without it pytest imports `conftest.py` as a top-level module and the shared fixtures and
constants have two names depending on how the suite was invoked.
"""
