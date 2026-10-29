"""Task routing and scope observations; never an authorization credential."""
from __future__ import annotations

import argparse
import json
import re
import stat
from pathlib import Path
from typing import Any

_MARKER = re.compile(r"<!-- agent-first-routes\s*\n(.*?)\n-->", re.S)


def _direct_info(path: Path, kind: str) -> Any:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"indirect task-record {kind}")
    return info


def _plan_records(directory: Path) -> list[Path]:
    """Only legacy root records and one task-directory level are discoverable."""
    for parent in (directory, *directory.parents):
        try:
            _direct_info(parent, "directory")
        except FileNotFoundError:
            continue
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError("invalid task-record directory")
    records: list[Path] = []
    for entry in sorted(directory.iterdir()):
        info = _direct_info(entry, "entry")
        if entry.name.startswith("[PLAN]_") and entry.suffix == ".md":
            records.append(entry)
        elif stat.S_ISDIR(info.st_mode) and entry.name != "archive":
            plans = [path for path in sorted(entry.iterdir())
                     if path.name.startswith("[PLAN]_") and path.suffix == ".md"]
            if len(plans) > 1 or (plans and plans[0].name != f"[PLAN]_{entry.name}.md"):
                raise ValueError("ambiguous task-directory main Plan")
            records.extend(plans)
    return records


def _validate_route(route: Any) -> None:
    if not isinstance(route, dict):
        raise ValueError("invalid task route")
    task = route.get("task_id")
    children = route.get("children")
    if (not isinstance(task, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", task)
            or route.get("integration") != f"feature/task-{task}-integration"
            or route.get("mainline") != "develop"
            or not isinstance(route.get("repo"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", route["repo"])
            or not isinstance(children, list) or not children
            or not all(isinstance(child, str) and re.fullmatch(r"(?:feature|bugfix|documentation|maintain|hotfix)/[a-z0-9][a-z0-9-]*", child) for child in children)
            or len(set(children)) != len(children)
            or not isinstance(route.get("active"), bool)):
        raise ValueError("invalid task route fields")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate task routing field")
        result[key] = value
    return result


def load_task_routes(root: Path) -> list[dict[str, Any]]:
    """Read bounded routing blocks in existing Plan records, not private config."""
    routes: list[dict[str, Any]] = []
    for path in _plan_records(root / "plans"):
        info = _direct_info(path, "file")
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("invalid task record")
        if info.st_size > 1024 * 1024:
            raise ValueError("task record exceeds limit")
        content = path.read_text(encoding="utf-8")
        blocks = _MARKER.findall(content)
        if len(blocks) > 1 or content.count("<!-- agent-first-routes") != len(blocks):
            raise ValueError("ambiguous task record")
        for block in blocks:
            payload = json.loads(block, object_pairs_hook=_unique_object)
            if (not isinstance(payload, dict) or type(payload.get("schema_version")) is not int
                    or payload["schema_version"] != 1 or not isinstance(payload.get("routes"), list)):
                raise ValueError("invalid task routing block")
            for route in payload["routes"]:
                _validate_route(route)
            routes.extend(payload["routes"])
    relations: set[tuple[str, str, str]] = set()
    for route in routes:
        if route["active"]:
            for child in route["children"]:
                key = (route["repo"], child, route["integration"])
                if key in relations:
                    raise ValueError("ambiguous task route")
                relations.add(key)
    return routes


def valid_pr_base(repo: str, head: str, base: str, routes: list[dict[str, Any]]) -> bool:
    """Exact registered relations supplement the normal mainline rule."""
    head = head.removeprefix("refs/heads/")
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", head) or '..' in head or '//' in head
            or head.endswith('/') or any(part.startswith('.') or part.endswith(('.', '.lock')) for part in head.split('/'))):
        return False
    for route in routes:
        _validate_route(route)
    if base == ("main" if head.startswith("hotfix/") else "develop"):
        return True
    matches = []
    for route in routes:
        integration = route.get("integration")
        children = route.get("children")
        if route.get("active") is not True or route.get("repo") != repo:
            continue
        if head in children and base == integration:
            matches.append(route)
    if len(matches) > 1:
        raise ValueError("ambiguous task route")
    return len(matches) == 1


def main(argv: list[str] | None = None) -> int:
    """Block unsupported actual PR routes; this does not authenticate authorization."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
            raise ValueError("repository identity unavailable")
        allowed = valid_pr_base(args.repo, args.head, args.base, load_task_routes(args.root))
    except (OSError, ValueError, TypeError):
        print(json.dumps({"state": "UNKNOWN", "authorization": "NOT_ASSESSED"}))
        return 2
    print(json.dumps({"state": "ROUTE_VALID" if allowed else "FORBIDDEN", "authorization": "NOT_ASSESSED"}))
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
