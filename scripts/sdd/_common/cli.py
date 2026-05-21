"""scripts/sdd/_common/cli.py — shared CLI scaffolding for SDD validators.

Provides:
- `Severity` enum (str-based; interop with plain strings).
- `Summary` dataclass tracking PASS/WARN/FAIL counts + messages.
- `build_argparser()` factory producing the canonical `--dry-run / --capability /
  --all / --strict` flag set.

Phase M2 (per blueprint §6 Phase M2 §3 + ADR-031 §5). All 6 sdd validators
import from here to avoid duplicating ~80 lines of boilerplate per script.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Severity(StrEnum):
    """Validator finding severity. str-based so interop with plain strings."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class Summary:
    """Aggregate validator findings across a single contract or full run."""

    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    messages: list[str] = field(default_factory=list)

    def add(self, severity: Severity, message: str) -> None:
        """Add a single finding (counts += 1; message appended)."""
        self.messages.append(f"  [{severity.value}] {message}")
        if severity is Severity.PASS:
            self.pass_count += 1
        elif severity is Severity.WARN:
            self.warn_count += 1
        elif severity is Severity.FAIL:
            self.fail_count += 1

    def add_aggregate_pass(self, n: int, message: str | None = None) -> None:
        """Add `n` to pass_count (for batch verification like 'N modules verified')."""
        self.pass_count += n
        if message:
            self.messages.append(f"  [PASS] {message}")

    def merge(self, other: Summary) -> None:
        """Merge counts only; messages are printed inline per contract."""
        self.pass_count += other.pass_count
        self.warn_count += other.warn_count
        self.fail_count += other.fail_count

    def print_messages(self) -> None:
        """Print all collected messages to stdout."""
        for msg in self.messages:
            print(msg)

    def exit_code(self, strict: bool = False) -> int:
        """Return exit code: 1 on FAIL; 1 on WARN when strict; else 0."""
        if self.fail_count > 0:
            return 1
        if strict and self.warn_count > 0:
            return 1
        return 0


def build_argparser(
    script_name: str, description: str, contract_filename: str
) -> argparse.ArgumentParser:
    """Build the canonical sdd validator argparser.

    All sdd validators support the same flag set:
    - `--dry-run`: discovery only; no validation logic runs.
    - `--capability <path>`: validate one capability dir.
    - `--all`: validate all discovered contracts (default behavior).
    - `--strict`: exit 1 on WARN (Phase M3 blocking mode).

    `contract_filename` is informational (validator decides which file to glob);
    surfaced in `--help` output as the discovery target.
    """
    parser = argparse.ArgumentParser(prog=script_name, description=description)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=f"discovery only; print count of {contract_filename} found, no validation",
    )
    parser.add_argument(
        "--capability",
        type=Path,
        help="validate one capability dir (e.g. capabilities/data-agent/safe-sql)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="validate all discovered contracts (default behavior)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on WARN (Phase M3 blocking mode)",
    )
    return parser


__all__ = ["Severity", "Summary", "build_argparser"]
