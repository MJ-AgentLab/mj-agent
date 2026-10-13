"""Task routing and scope observations; never an authorization credential."""
from __future__ import annotations

import argparse
import json
import re
import stat
from pathlib import Path
from typing import Any

_MARKER = re.compile(r"<!-- agent-first-routes\s*\n(.*?)\n-->", re.S)


def load_task_routes(root: Path) -> list[dict[str, Any]]:
    """Read bounded routing blocks in existing Plan records, not private config."""
    routes: list[dict[str, Any]] = []
    directory = root / "plans"
    for parent in (directory, *directory.parents):
        if not parent.exists():
            continue
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("indirect task-record directory")
    for path in sorted(directory.glob("[[]PLAN[]]_*.md")):
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise ValueError("indirect task record")
        if info.st_size > 1024 * 1024:
            raise ValueError("task record exceeds limit")
        blocks = _MARKER.findall(path.read_text(encoding="utf-8"))
        if len(blocks) > 1:
            raise ValueError("ambiguous task record")
        for block in blocks:
            payload = json.loads(block)
            if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("routes"), list):
                raise ValueError("invalid task routing block")
            routes.extend(payload["routes"])
    return routes


def valid_pr_base(repo: str, head: str, base: str, routes: list[dict[str, Any]]) -> bool:
    """Exact registered relations supplement the normal mainline rule."""
    head = head.removeprefix("refs/heads/")
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", head) or '..' in head or '//' in head
            or head.endswith('/') or any(part.startswith('.') or part.endswith(('.', '.lock')) for part in head.split('/'))):
        return False
    if base == ("main" if head.startswith("hotfix/") else "develop"):
        return True
    matches = []
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("invalid task route")
        task = route.get("task_id")
        integration = route.get("integration")
        children = route.get("children")
        if (not isinstance(task, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", task)
                or integration != f"feature/task-{task}-integration"
                or route.get("mainline") != "develop"
                or not isinstance(children, list) or not children
                or not all(isinstance(child, str) and re.fullmatch(r"(?:feature|bugfix|documentation|maintain|hotfix)/[a-z0-9][a-z0-9-]*", child) for child in children)
                or len(set(children)) != len(children)
                or not isinstance(route.get("active"), bool)):
            raise ValueError("invalid task route fields")
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
