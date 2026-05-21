"""scripts/sdd/_common — shared helpers for the 6 SDD validators.

Per Phase M2 Stage A augmentation #3 (`_common/__init__.py` 显式 re-export +
`__all__`): 6 validators import directly from this package to avoid long
`from scripts.sdd._common.<submodule> import ...` chains.

Module layout:
- `cli`         — Severity / Summary / build_argparser
- `discovery`   — discover_contracts / resolve_display_path
- `yaml_io`     — load_contract / validate_contract_id
- `ast_helpers` — module_path_to_file / parse_module_safe / extract_top_level_names
                  / check_constant_literal
- `frontmatter` — parse_frontmatter / strip_frontmatter / body_sha256 /
                  extract_headings (with doctest)
- `enums`       — HITL_CANONICAL / validate_hitl_enum
"""

from __future__ import annotations

from scripts.sdd._common.ast_helpers import (
    check_constant_literal,
    extract_top_level_names,
    module_path_to_file,
    parse_module_safe,
)
from scripts.sdd._common.cli import Severity, Summary, build_argparser
from scripts.sdd._common.discovery import discover_contracts, resolve_display_path
from scripts.sdd._common.enums import HITL_CANONICAL, validate_hitl_enum
from scripts.sdd._common.frontmatter import (
    body_sha256,
    extract_headings,
    parse_frontmatter,
    strip_frontmatter,
)
from scripts.sdd._common.yaml_io import load_contract, validate_contract_id

__all__ = [
    # cli (3)
    "Severity",
    "Summary",
    "build_argparser",
    # discovery (2)
    "discover_contracts",
    "resolve_display_path",
    # yaml_io (2)
    "load_contract",
    "validate_contract_id",
    # ast_helpers (4)
    "module_path_to_file",
    "parse_module_safe",
    "extract_top_level_names",
    "check_constant_literal",
    # frontmatter (4)
    "parse_frontmatter",
    "strip_frontmatter",
    "body_sha256",
    "extract_headings",
    # enums (2)
    "HITL_CANONICAL",
    "validate_hitl_enum",
]
