#!/usr/bin/env python3
"""Retired working-document GC entry point (Issue #608).

Completed working documents remain at their task paths. The former age-based
candidate scan and physical archive workflow are no longer active. This
compatibility entry point never scans, moves, deletes, or changes metadata.
Canonical archive policy is independent of this retired working workflow.
"""
from __future__ import annotations

import sys


def main() -> int:
    print("RETIRED: working-document GC and candidate detection are disabled; keep completed artifacts in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())
