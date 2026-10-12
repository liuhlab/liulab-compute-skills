"""Tests for `scripts/upstream_sync.py`, the upstream sync's merge-and-report step.

Each test builds an upstream and a lab tree as git repos in its own temporary directory and
drives the script at its command line, then reads what a maintainer would: the files it
wrote, the report it printed and its exit status. Nothing here reaches the network.
"""
