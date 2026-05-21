"""scripts/ — mj-agent CLI scripts package marker.

Added Phase M2 to resolve mypy 'Source file found twice under different module
names' ambiguity for `scripts.sdd._common` imports. Empty marker; existing
top-level scripts (`scripts/check_frontmatter.py` etc.) remain invokable as
`uv run python scripts/<name>.py` (file path) unchanged.
"""

__all__: list[str] = []
