"""DISABLED — live biz-schema capture is retired (Epic #499 PR-0c).

This script used to open a direct connection to the business warehouse and snapshot
``biz_dws`` / ``biz_dwd`` schemas to YAML. That route bypassed the sanctioned agent
tool-chain and the L1/L1b SQL guardrails, and it required analyst credentials in the
process environment. Both are prohibited by the data boundary (ADR-006 / ADR-009 /
ADR-000, root ``AGENTS.md`` boundary 1).

It is now a **fail-closed tombstone**: it imports no dotenv, no database client and no
introspection wrapper, it can produce no output, and it exits ``2`` for every argv shape.
There is deliberately no flag that re-enables the old behaviour.

To obtain biz schema facts, use the sanctioned agent tool-chain instead::

    find_biz_context -> list_biz_tables -> describe_biz_table -> execute_sql

To run catalog drift detection offline, place an Owner-attested sanitized snapshot under
``.mj-agent-local/biz-schema-snapshots/`` (gitignored) and run::

    uv run python scripts/diff_biz_schema.py --snapshot <name>.yaml

``scripts/diff_biz_schema.py`` reads only that root, validates the closed ``schema-v1``
envelope, and emits ``SKIP_NO_SNAPSHOT`` / ``SKIP_STALE_SNAPSHOT`` rather than pretending
the catalog is current.
"""

from __future__ import annotations

import sys

#: Exit status for "this route is permanently disabled". Never 0 (which a caller would
#: read as success) and never 1 (which ``diff_biz_schema.py`` uses for real drift).
EXIT_DISABLED = 2

_GUIDANCE = """\
[fetch_biz_schema] DISABLED - direct biz-DB capture is retired (Epic #499 PR-0c).

This script no longer connects to any database and produces no output.

  Sanctioned route for biz schema facts (agent tool-chain, read-only `analyst` role):
      find_biz_context -> list_biz_tables -> describe_biz_table -> execute_sql

  Offline catalog drift detection:
      1. Place an Owner-attested sanitized snapshot in
         .mj-agent-local/biz-schema-snapshots/   (gitignored; never committed)
      2. uv run python scripts/diff_biz_schema.py --snapshot <name>.yaml

  Rationale: the old route bypassed the L1/L1b SQL guardrails and required analyst
  credentials in the environment (ADR-006 / ADR-009 / ADR-000; AGENTS.md boundary 1).
"""


def main(argv: list[str] | None = None) -> int:
    """Print sanctioned-route guidance and fail closed.

    ``argv`` is accepted and deliberately ignored: no argument combination may revive the
    retired route, so there is nothing to parse.
    """
    del argv
    print(_GUIDANCE, file=sys.stderr)
    return EXIT_DISABLED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
