#!/usr/bin/env python3
"""MIST build script."""

import os
import sys
import subprocess


def run(cmd: str) -> int:
    print(f"  > {cmd}")
    return subprocess.call(cmd, shell=True)


def build():
    print("=== MIST Build ===")

    print("\n[1/4] Checking requirements...")
    if run("python -m pip install -r requirements.txt --quiet"):
        print("WARNING: pip install failed")

    print("\n[2/4] Running tests...")
    if run("python -m pytest tests/ -q"):
        print("ERROR: Tests failed")
        sys.exit(1)

    print("\n[3/4] Checking imports...")
    if run("python -c \"import main\""):
        print("WARNING: Import check failed")

    print("\n[4/4] Build complete!")
    print("=== OK ===")


if __name__ == "__main__":
    build()
