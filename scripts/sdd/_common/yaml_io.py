"""scripts/sdd/_common/yaml_io.py — YAML contract loading + identity validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_contract(contract_path: Path) -> dict[str, Any] | None:
    """Load contract YAML. Return dict on success; None on parse error or non-mapping root."""
    try:
        with contract_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def validate_contract_id(contract: dict[str, Any], expected: str) -> bool:
    """Return True iff `contract['contract_id'] == expected`."""
    return contract.get("contract_id") == expected


__all__ = ["load_contract", "validate_contract_id"]
