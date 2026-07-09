#!/usr/bin/env python3
"""Quick script to get clean violation list."""
import subprocess
import sys

result = subprocess.run(
    ["python", "scripts/lint_check.py", "src"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
