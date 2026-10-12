"""Private offline core, deliberately separate from the deferred CLI entry."""

from __future__ import annotations

from typing import Any

from .judges import _judge
from .report import _markdown, _summarize
from .schema import _INPUT_ERRORS, _Inputs, _Invalid, _load


def _replay(inputs: _Inputs) -> dict[str, Any]:
    """Judge explicit in-memory bytes. No file, network or application access."""
    try:
        bundle = _load(inputs)
        cases = [_judge(bundle, case) for case in bundle.cases]
        report = _summarize(bundle, cases)
        report["markdown"] = _markdown(report)
        return report
    except _INPUT_ERRORS as exc:
        reason = str(exc) if isinstance(exc, _Invalid) else "INVALID_INPUT_SCHEMA"
        return {
            "schema_version": "offline-report-v1", "exit_code": 2,
            "input_status": "INPUT_INVALID", "reason_code": reason,
            "cases": [], "measurement": {"status": "NOT_MEASURED", "metrics": None},
            "safety": {"status": "UNDETERMINED", "failed_cases": []},
            "regression": {"status": "NOT_EVALUATED", "delta": None},
            "baseline_eligible": False,
            "limitations": ["OFFLINE_REPLAY_ONLY", "CLI_ENTRY_DEFERRED"],
        }
