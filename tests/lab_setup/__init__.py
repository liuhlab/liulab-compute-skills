"""Tests for `skills/lab-setup/scripts/lab_setup.py`, the mechanical half of `/lab-setup`.

Every test drives the script at its command line against a fake home in `tmp_path`, and
asserts on what a member would see: the files it leaves, the lines it prints, its exit
status. None touches the real home, the network or a pixi environment.
"""
