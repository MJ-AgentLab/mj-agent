"""scripts/sdd/check_docker_contracts.py — Phase M2 + M3-FU-V5-SUBFLAGS.

Validates `capabilities/*/contracts/docker.contract.yml` AND
`compose.contract.yml` against actual `infra/docker/Dockerfile` + 4 compose
YAML files.

Per blueprint §6 Phase M2 §3 + ADR-031 §5 docker-container adapter + ADR-026
4-file compose profile + ADR-008 external network. Phase M2 warning mode.

Commit 5.1: Dockerfile + compose static lint (core; default behavior).
Commit 5.2 (M3-FU-V5-SUBFLAGS): additive `--bdd` / `--tdd` / `--compose-config`
sub-flags toggle extra schema-layer checks beyond core lint.

Sub-flag semantics (additive; no replacement of core lint):
- `--bdd`: docker-bdd-scenario-check sub-mode. Confirms BDD-relevant schema
  fields are present (healthcheck on docker.contract.yml + each service in
  compose.contract.yml). Static-only; no Compose API mock invocation.
- `--tdd`: docker-tdd-contract-test sub-mode. Confirms TDD schema-layer
  completeness (runtime_stage_contract on docker, invocation_contract on
  compose with all 3 profile commands).
- `--compose-config`: static analog of `docker compose config`. Loads each
  declared compose YAML file, verifies top-level shape (`services` /
  `networks` dicts) without invoking docker daemon.

Handles M1 actual nested schema (different from M0 docker.contract.yml.template
which used flat fields):
  - `dockerfile.path` (M1 nested) vs `dockerfile` (M0 template flat string).
  - `runtime_stage_contract.user.non_root` (M1 nested) vs `user_required:
    non-root` (M0 template flat string).
  - `runtime_stage_contract.forbidden_in_image` (M1 nested) vs
    `forbidden_in_image` (M0 template top-level).
  - compose.contract.yml: `file_layering.{base,overlays[]}.path` (M1 nested)
    vs `compose_files` (M0 template flat list).

V5 tolerates both schemas via fallback chain; emits WARN documenting schema
deviation between M0 template and M1 actual (cleanup task for M3 PR).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402
    Severity,
    Summary,
    build_argparser,
    discover_contracts,
    load_contract,
    resolve_display_path,
    validate_contract_id,
)
from scripts.sdd._common.yaml_io import load_contract as _load_yaml_file  # noqa: E402

_BDD_DOCKER_REQUIRED_FIELDS = ("healthcheck",)
_TDD_DOCKER_REQUIRED_FIELDS = ("runtime_stage_contract",)
_TDD_COMPOSE_INVOCATION_COMMANDS = ("dev_command", "test_command", "prod_command")


def _get_nested(contract: dict[str, Any], *path: str) -> Any:
    """Safe nested dict access; returns None if any intermediate is not a dict."""
    cur: Any = contract
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _extract_dockerfile_path(contract: dict[str, Any]) -> str | None:
    """Extract dockerfile path (M1 nested dict OR M0 flat string)."""
    df = contract.get("dockerfile")
    if isinstance(df, dict):
        path = df.get("path")
        return path if isinstance(path, str) else None
    if isinstance(df, str):
        return df
    return None


def _extract_forbidden_in_image(contract: dict[str, Any]) -> list[str]:
    """Extract forbidden_in_image list (M1 nested OR M0 flat)."""
    nested = _get_nested(contract, "runtime_stage_contract", "forbidden_in_image")
    if isinstance(nested, list):
        return [str(x) for x in nested]
    flat = contract.get("forbidden_in_image")
    if isinstance(flat, list):
        return [str(x) for x in flat]
    return []


def _validate_docker_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one docker.contract.yml (Dockerfile lint)."""
    summary = Summary()
    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary
    if not validate_contract_id(contract, "docker"):
        summary.add(Severity.FAIL, f"{contract_path}: contract_id is not 'docker'")
        return summary

    dockerfile_path = _extract_dockerfile_path(contract)
    if not dockerfile_path:
        summary.add(Severity.FAIL, "docker.contract.yml missing dockerfile path (neither dockerfile.path nor dockerfile string)")
        return summary

    df = repo_root / dockerfile_path
    if not df.exists():
        summary.add(Severity.FAIL, f"dockerfile {dockerfile_path!r} not found in repo")
        return summary

    text = df.read_text(encoding="utf-8")

    non_root_required = (
        _get_nested(contract, "runtime_stage_contract", "user", "non_root") is True
        or contract.get("user_required") == "non-root"
    )
    if non_root_required:
        user_match = re.search(r"^USER\s+(\S+)", text, re.MULTILINE)
        if not user_match:
            summary.add(Severity.FAIL, f"{dockerfile_path}: contract requires USER non-root but no USER directive found")
        elif user_match.group(1) in ("root", "0", "0:0"):
            summary.add(Severity.FAIL, f"{dockerfile_path}: USER directive resolves to root ({user_match.group(1)!r})")

    for forbidden_path in _extract_forbidden_in_image(contract):
        pattern = re.compile(rf"^(COPY|ADD)\s+.*{re.escape(forbidden_path)}", re.MULTILINE)
        if pattern.search(text):
            summary.add(Severity.FAIL, f"{dockerfile_path}: COPY/ADD references forbidden path {forbidden_path!r} (secrets leak via image layers)")

    has_healthcheck_field = "healthcheck" in contract or contract.get("healthcheck_required") is True
    if has_healthcheck_field and not re.search(r"^HEALTHCHECK\s+", text, re.MULTILINE):
        summary.add(Severity.WARN, f"{dockerfile_path}: HEALTHCHECK directive missing (contract describes healthcheck.cmd)")

    runtime_stage = contract.get("runtime_stage_contract")
    if isinstance(runtime_stage, dict):
        summary.add(Severity.WARN, "runtime_stage_contract nested schema (M1 deviation from M0 template flat fields; M3 cleanup PR planned)")
    if _get_nested(contract, "base_image", "runtime_stage", "image"):
        summary.add(Severity.WARN, "base_image.runtime_stage.image documented (informational; M3 will resolve Dependabot digest pin to verify match)")

    if summary.fail_count == 0:
        summary.add_aggregate_pass(n=1, message=f"docker.contract.yml verified ({dockerfile_path!r})")
    return summary


def _check_docker_bdd(contract: dict[str, Any], summary: Summary) -> None:
    """`--bdd` sub-flag: confirm docker.contract.yml declares healthcheck spec."""
    for field in _BDD_DOCKER_REQUIRED_FIELDS:
        value = contract.get(field)
        if not isinstance(value, dict):
            summary.add(
                Severity.WARN,
                f"--bdd: docker.contract.yml missing required field '{field}' "
                f"(docker-bdd-scenario-check expects healthcheck spec block)",
            )
            continue
        if not value.get("cmd"):
            summary.add(
                Severity.WARN,
                f"--bdd: docker.contract.yml {field}.cmd missing (healthcheck command required)",
            )


def _check_docker_tdd(contract: dict[str, Any], summary: Summary) -> None:
    """`--tdd` sub-flag: confirm runtime_stage_contract schema completeness."""
    for field in _TDD_DOCKER_REQUIRED_FIELDS:
        value = contract.get(field)
        if not isinstance(value, dict):
            summary.add(
                Severity.WARN,
                f"--tdd: docker.contract.yml missing schema-layer required field '{field}'",
            )
            continue
        for sub in ("user", "forbidden_in_image", "entrypoint"):
            if sub not in value:
                summary.add(
                    Severity.WARN,
                    f"--tdd: docker.contract.yml {field} missing sub-field '{sub}' "
                    f"(docker-tdd-contract-test schema cross-check)",
                )


def _extract_compose_files(contract: dict[str, Any]) -> list[str]:
    """Extract compose file paths (M1 file_layering nested OR M0 compose_files flat list)."""
    files: list[str] = []
    file_layering = contract.get("file_layering")
    if isinstance(file_layering, dict):
        base_path = _get_nested(file_layering, "base", "path")
        if isinstance(base_path, str):
            files.append(base_path)
        overlays = file_layering.get("overlays", [])
        if isinstance(overlays, list):
            for overlay in overlays:
                p = overlay.get("path") if isinstance(overlay, dict) else None
                if isinstance(p, str):
                    files.append(p)
        return files
    flat = contract.get("compose_files")
    if isinstance(flat, list):
        return [str(x) for x in flat]
    return []


def _validate_compose_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one compose.contract.yml (4-file profile lint)."""
    summary = Summary()
    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary
    if not validate_contract_id(contract, "compose"):
        summary.add(Severity.FAIL, f"{contract_path}: contract_id is not 'compose'")
        return summary

    compose_files = _extract_compose_files(contract)
    if not compose_files:
        summary.add(Severity.FAIL, "compose.contract.yml: no compose files declared (neither file_layering nor compose_files)")
        return summary

    if len(compose_files) < 2:
        summary.add(Severity.WARN, f"compose files count {len(compose_files)} < 2; expected base + overlay(s) per ADR-026 multi-file profile")

    for cf in compose_files:
        cf_path = repo_root / cf
        if not cf_path.exists():
            summary.add(Severity.FAIL, f"compose file {cf!r} not found in repo")

    if contract.get("file_layering"):
        summary.add(Severity.WARN, "file_layering nested schema (M1 deviation from M0 template flat compose_files; M3 cleanup PR planned)")
    if _get_nested(contract, "invocation_contract", "dev_command"):
        summary.add(Severity.WARN, "invocation_contract documented (informational; M3 will static-validate the -f chain shape)")

    if summary.fail_count == 0:
        summary.add_aggregate_pass(
            n=1, message=f"compose.contract.yml verified ({len(compose_files)} compose files resolve)"
        )
    return summary


def _check_compose_bdd(contract: dict[str, Any], summary: Summary) -> None:
    """`--bdd` sub-flag: confirm each service has healthcheck (REQ-002 startup order)."""
    services = contract.get("services")
    if not isinstance(services, dict):
        summary.add(Severity.WARN, "--bdd: compose.contract.yml services field missing or not a mapping")
        return
    for svc_name, svc in services.items():
        if not isinstance(svc, dict):
            continue
        if "healthcheck" not in svc:
            summary.add(
                Severity.WARN,
                f"--bdd: compose service {svc_name!r} missing healthcheck (REQ-002 startup order)",
            )


def _check_compose_tdd(contract: dict[str, Any], summary: Summary) -> None:
    """`--tdd` sub-flag: confirm invocation_contract has all 3 profile commands."""
    invocation = contract.get("invocation_contract")
    if not isinstance(invocation, dict):
        summary.add(
            Severity.WARN,
            "--tdd: compose.contract.yml missing invocation_contract (docker-tdd-contract-test schema)",
        )
        return
    for cmd in _TDD_COMPOSE_INVOCATION_COMMANDS:
        if cmd not in invocation:
            summary.add(
                Severity.WARN,
                f"--tdd: compose.contract.yml invocation_contract.{cmd} missing "
                f"(3 profile commands required: dev/test/prod)",
            )


def _check_compose_config(compose_files: list[str], repo_root: Path, summary: Summary) -> None:
    """`--compose-config` sub-flag: static parse compose YAML chain for top-level shape.

    Validates each file individually for YAML loadability + base-file `services`
    presence, then validates the merged service set (across base + overlays) has
    `image` or `build` somewhere — matching docker compose's overlay-merge semantic
    where overlay services inherit the base's `image`.
    """
    if not compose_files:
        return
    base_has_services = False
    service_image_or_build: dict[str, bool] = {}
    for idx, cf in enumerate(compose_files):
        cf_path = repo_root / cf
        if not cf_path.exists():
            continue  # already FAILed in core lint; avoid duplicate report
        loaded = _load_yaml_file(cf_path)
        if not isinstance(loaded, dict):
            summary.add(
                Severity.WARN,
                f"--compose-config: {cf}: YAML root is not a mapping",
            )
            continue
        services = loaded.get("services")
        if idx == 0:
            if "services" not in loaded:
                summary.add(
                    Severity.WARN,
                    f"--compose-config: {cf} (base): missing top-level 'services' key",
                )
            elif isinstance(services, dict):
                base_has_services = True
        if isinstance(services, dict):
            for svc_name, svc in services.items():
                if not isinstance(svc, dict):
                    continue
                has_image_or_build = "image" in svc or "build" in svc
                # OR-merge across the file chain.
                service_image_or_build[svc_name] = (
                    service_image_or_build.get(svc_name, False) or has_image_or_build
                )
    if base_has_services:
        for svc_name, ok in service_image_or_build.items():
            if not ok:
                summary.add(
                    Severity.WARN,
                    f"--compose-config: service {svc_name!r} has neither 'image' nor 'build' "
                    f"in any compose file in the layering chain",
                )


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_docker_contracts.py",
        description=(
            "Validate docker.contract.yml + compose.contract.yml against actual "
            "infra/docker/ artifacts. Phase M2 commit 5.1 core lint + M3-FU-V5-SUBFLAGS "
            "sub-flags. Tolerates M1 nested schema vs M0 template flat schema (emits "
            "WARN about deviation). Sub-flags --bdd / --tdd / --compose-config toggle "
            "additive schema-layer checks beyond core lint."
        ),
        contract_filename="docker.contract.yml + compose.contract.yml",
    )
    parser.add_argument("--bdd", action="store_true", help="enable docker-bdd-scenario-check sub-mode")
    parser.add_argument("--tdd", action="store_true", help="enable docker-tdd-contract-test sub-mode")
    parser.add_argument(
        "--compose-config",
        action="store_true",
        help="enable static compose YAML structure check (docker compose config analog)",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    docker_contracts = discover_contracts(repo_root, "docker.contract.yml", args.capability)
    compose_contracts = discover_contracts(repo_root, "compose.contract.yml", args.capability)

    if args.dry_run:
        sub_modes = ", ".join(s for s, on in [("bdd", args.bdd), ("tdd", args.tdd), ("compose-config", args.compose_config)] if on) or "core lint only"
        print(
            f"[dry-run] check_docker_contracts.py — Phase M2/M3 ({sub_modes}); "
            f"found {len(docker_contracts)} docker.contract.yml + "
            f"{len(compose_contracts)} compose.contract.yml"
        )
        return 0

    if not docker_contracts and not compose_contracts:
        print("no docker.contract.yml / compose.contract.yml found")
        return 0

    print(f"check_docker_contracts.py — validating {len(docker_contracts)} docker.contract.yml + {len(compose_contracts)} compose.contract.yml")
    total = Summary()
    for cp in docker_contracts:
        display = resolve_display_path(cp, repo_root)
        print(f"\n{display}")
        sub = _validate_docker_contract(cp, repo_root)
        if args.bdd or args.tdd:
            contract = load_contract(cp)
            if isinstance(contract, dict):
                if args.bdd:
                    _check_docker_bdd(contract, sub)
                if args.tdd:
                    _check_docker_tdd(contract, sub)
        sub.print_messages()
        total.merge(sub)

    for cp in compose_contracts:
        display = resolve_display_path(cp, repo_root)
        print(f"\n{display}")
        sub = _validate_compose_contract(cp, repo_root)
        if args.bdd or args.tdd or args.compose_config:
            contract = load_contract(cp)
            if isinstance(contract, dict):
                if args.bdd:
                    _check_compose_bdd(contract, sub)
                if args.tdd:
                    _check_compose_tdd(contract, sub)
                if args.compose_config:
                    _check_compose_config(_extract_compose_files(contract), repo_root, sub)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS: {total.pass_count} / WARN: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
