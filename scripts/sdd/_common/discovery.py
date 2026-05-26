"""scripts/sdd/_common/discovery.py — capability contract discovery + path display."""

from __future__ import annotations

from pathlib import Path


def discover_contracts(
    repo_root: Path,
    contract_filename: str,
    capability_arg: Path | None = None,
) -> list[Path]:
    """Discover capability contract files.

    If `capability_arg` is provided, look for the single contract at
    `<capability_arg>/contracts/<contract_filename>`. Otherwise glob all
    `capabilities/*/*/contracts/<contract_filename>`.
    """
    if capability_arg is not None:
        candidate = (capability_arg / "contracts" / contract_filename).resolve()
        return [candidate] if candidate.exists() else []
    capabilities_dir = repo_root / "capabilities"
    if not capabilities_dir.exists():
        return []
    return sorted(capabilities_dir.glob(f"*/*/contracts/{contract_filename}"))


def resolve_display_path(path: Path, repo_root: Path) -> str:
    """Return display string: relative to repo_root if possible; else absolute."""
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def discover_capabilities(
    repo_root: Path,
    capability_arg: Path | None = None,
) -> list[Path]:
    """Discover capability directories via ``spec.yml`` glob.

    Returns capability DIRS (not spec.yml file paths) so callers can access
    both ``<cap>/spec.yml`` and ``<cap>/evidence/`` from the same Path.

    If ``capability_arg`` is provided, look for the single
    ``<capability_arg>/spec.yml``. Otherwise glob
    ``capabilities/*/*/spec.yml`` parents.
    """
    if capability_arg is not None:
        candidate_spec = (capability_arg / "spec.yml").resolve()
        return [capability_arg] if candidate_spec.exists() else []
    capabilities_dir = repo_root / "capabilities"
    if not capabilities_dir.exists():
        return []
    return sorted(p.parent for p in capabilities_dir.glob("*/*/spec.yml"))


__all__ = ["discover_contracts", "discover_capabilities", "resolve_display_path"]
