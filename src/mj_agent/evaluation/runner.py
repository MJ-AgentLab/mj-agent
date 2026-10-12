"""Synthetic-only local CLI for the in-memory replay API; no runtime wiring."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path
from typing import Any, NoReturn

from ._file_io import _backend, _FileError, _relative, _root
from .core import replay
from .schema import _INPUT_ERRORS, ReplayInputs, _canonical, _Invalid, _json, _Manifest

_INPUT_OPTIONS = {"config": "--eval-config", "dataset": "--dataset", "observations": "--observations",
                  "manifest": "--manifest", "reference": "--reference", "reviews": "--reviews"}


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _FileError("CLI_ARGUMENT_INVALID")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="mj-agent-eval", description="Replay explicitly named synthetic fixtures only.",
                     allow_abbrev=False)
    parser.add_argument("--synthetic-fixture", required=True, action="store_true")
    for field, option in _INPUT_OPTIONS.items():
        parser.add_argument(option, dest=field, required=field != "reviews")
    parser.add_argument("--output-dir", required=True)
    return parser


def _report_files(report: dict[str, Any]) -> tuple[tuple[str, bytes], ...]:
    markdown = report.get("markdown")
    if not isinstance(markdown, str):
        markdown = ("# Offline EVAL input diagnostic\n\nInput: INPUT_INVALID\n"
                    f"Reason: {report['reason_code']}\nExit code: 2\n\n"
                    "Live sampling was not executed.\n")
    return (("report.json", _canonical(report)), ("report.md", markdown.encode("utf-8")))


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    """Read explicit synthetic files within one root; actual and baseline are deferred."""
    core_exit = None
    try:
        args = _parser().parse_args(argv)
        root = _root(repo_root)
        paths = {field: _relative(root, value) for field in _INPUT_OPTIONS
                 if (value := getattr(args, field)) is not None}
        output = _relative(root, args.output_dir)
        with closing(_backend(root)) as session:
            manifest_bytes = session.read(paths["manifest"])
            value = _json(manifest_bytes)
            if not isinstance(value, dict):
                raise _FileError("SOURCE_KIND_INVALID")
            if value.get("source_kind") == "runtime_observation":
                raise _FileError("ACTUAL_ENTRY_DEFERRED")
            if value.get("source_kind") != "synthetic_fixture":
                raise _FileError("SOURCE_KIND_INVALID")
            _Manifest.model_validate(value)
            values = {field: session.read(parts) for field, parts in paths.items() if field != "manifest"}
            report = replay(ReplayInputs(**values, manifest=manifest_bytes))
            core_exit = int(report["exit_code"])
            session.write(output, _report_files(report))
            return core_exit
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    except _FileError as exc:
        reason = str(exc)
    except _INPUT_ERRORS as exc:
        reason = str(exc) if isinstance(exc, _Invalid) else "INVALID_INPUT_SCHEMA"
    except OSError:
        reason = "OUTPUT_IO_FAILED" if core_exit is not None else "LOCAL_IO_REJECTED"
    except Exception:
        reason = "INTERNAL_ERROR"
    diagnostic: dict[str, Any] = {"input_status": "INPUT_INVALID", "reason_code": reason, "exit_code": 2}
    if core_exit is not None:
        diagnostic["core_exit_code"] = core_exit
    print(json.dumps(diagnostic, sort_keys=True), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
