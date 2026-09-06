"""Unit tests for `src/edison_cli`, the Edison spend path.

Their own directory, because `tests/` also holds the repo's bash suites — the static lint,
the machine preflight and the agent evals — and those are a different kind of test with a
different cost. Nothing here spends anything or opens a socket.
"""
