---
type: capability-design
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Design: MCP Server Inventory + Governance

> Phase M1 baseline (≤ 200 lines per R-G3). Per ADR-028 + ADR-030.

## §1 Context

Model Context Protocol (MCP) servers are Claude Code's external tool surface. Each MCP server is a process Claude Code can communicate with via stdio / SSE / HTTP. mj-agent's `.mcp.json` declares 13 servers:

- **1 first-party** (`github`) — Anthropic-published; PAT-based
- **2 third-party** (`serena` for LSP; `ssh-manager` for 9 SSH hosts)
- **10 first-party-wrapper** (10 pg entries, all routed via `.claude/scripts/pg-server-start.cmd`)

**Threats**：

1. Adding an untrusted third-party MCP → tool-call surface expands; potential data exfil
2. Wrapper script regression (e.g. Dependabot bumps community pg MCP) → all 10 pg entries affected
3. WAN URL not set → server starts with empty arg → confusing startup error
4. LAN sentinel default `REPLACE_WITH_*_PASSWORD` not overridden → silent auth failure
5. ssh-manager 9-host aggregation → one entry, 9 trust posture implications
6. Quarterly audit skipped → trust posture stale (community MCP becomes unmaintained)

**Non-threats** (out of scope; governed elsewhere):

- LLM endpoint connectivity → `data-agent.llm-provider` REQ-002
- pg endpoint deployment → `infrastructure.docker-compose` REQ-001
- MCP secrets bundle decryption → `infrastructure.secrets-pipeline` (Phase 2+) per ADR-030

## §2 Decision

**13-entry inventory + per-entry trust posture declaration + A14 PR gate + wrapper-script consolidation for pg entries + quarterly audit cycle**.

| Component | File | Purpose |
|---|---|---|
| Inventory | `.mcp.json` | 13 server entries (name + type + args + env) |
| Wrapper | `.claude/scripts/pg-server-start.cmd` | Cmd wrapper invoking pg-server-wrapper.mjs |
| JS wrapper | `.claude/scripts/pg-server-wrapper.mjs` | Node-based; URL override from env |
| Baseline | `docs/_baselines/pg_server_baseline.md` | SOR for wrapper behavior; quarterly diff |
| STANDARD | `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` | §4 PR template; §6 quarterly audit process |
| A14 gate | `.github/PULL_REQUEST_TEMPLATE.md` (PR body field) | Reviewer-checked at PR review time |

**Why wrapper script (10 pg entries) instead of 10 distinct configs**：

- Centralized credential read pattern (env override > sentinel)
- Single point for timeout / error format / retry logic
- Quarterly baseline diff against community pg MCP catches drift
- Per-entry args (URL override env var name) declarable in `.mcp.json`

**Why 4 WAN entries have no default URL** (intentional fail-loud)：

- WAN tunnels (FRP) are inherently per-deployment; no sensible default
- Forcing env override at startup makes misconfiguration visible immediately
- `setup-mcp-secrets.ps1` (per ADR-030) is the canonical way to populate WAN URLs

**Why 6 LAN/DEV entries have sentinel defaults**：

- Allow local development WITHOUT secrets bundle decryption (smoother first-clone experience)
- Sentinel `REPLACE_WITH_TEAM_*_PASSWORD` silently auth-fails → dev sees clear "password authentication failed" error
- ADR-030 `setup-mcp-secrets.ps1` populates env overrides; subsequent restart fixes

## §3 Architecture

```
.mcp.json (13 entries)
├─► github                      [stdio]     first-party        API key env (GITHUB_PERSONAL_ACCESS_TOKEN)
├─► serena                      [stdio]     third-party        none (local-only LSP)
├─► pg-mj-agent-memory-dev      [stdio] ────► .claude/scripts/pg-server-start.cmd
├─► pg-mj-agent-memory-test-lan [stdio] ────►    └─► .claude/scripts/pg-server-wrapper.mjs
├─► pg-mj-agent-memory-test-wan [stdio] ────►          ├─► reads MJ_AGENT_PG_MEMORY_*_URL env override
├─► pg-mj-agent-memory-prod-lan [stdio] ────►          ├─► falls back to default (LAN/DEV) or empty (WAN)
├─► pg-mj-agent-memory-prod-wan [stdio] ────►          └─► invokes community pg MCP server with URL
├─► pg-mj-system-biz-dev        [stdio] ────►
├─► pg-mj-system-biz-test-lan   [stdio] ────►
├─► pg-mj-system-biz-test-wan   [stdio] ────►
├─► pg-mj-system-biz-prod-lan   [stdio] ────►
├─► pg-mj-system-biz-prod-wan   [stdio] ────►
└─► ssh-manager                 [stdio]     third-party        5 unique passwords via env:
                                                                 MJ_AGENT_SSH_SERVER_CLOUD_PASSWORD
                                                                 MJ_AGENT_SSH_SERVER_RUNNER_PASSWORD
                                                                 MJ_AGENT_SSH_SERVER_TEST_PASSWORD
                                                                 MJ_AGENT_SSH_SERVER_PROD_PASSWORD
                                                                 MJ_AGENT_SSH_SERVER_DGX_PASSWORD
                                                               (aggregates 9 SSH hosts: Cloud / Runner LAN/WAN /
                                                                Test LAN/WAN / Prod LAN/WAN / DGX-Spark LAN/WAN)

A14 PR Gate (Phase M3+ blocking):
  PR body §4 template (per MCP STANDARD)
    └─► declares per-entry trust_posture + credential_mode + rationale
       └─► reviewer ensures every changed entry has the block
          └─► CI: scripts/sdd/check_a14_gate.py (Phase M3+)

Quarterly Audit (§6 of MCP STANDARD):
  └─► DRI re-evaluates trust_posture of each server
     └─► diff .claude/scripts/pg-server-* against docs/_baselines/pg_server_baseline.md
        └─► if drift: file ADR for posture upgrade or wrapper baseline refresh
```

**Cross-capability dependencies (2 refs)**：

- `infrastructure.docker-compose` (inbound)：5 `pg-mj-agent-memory-*` entries connect to `mj-agent-postgres` deployed by docker-compose; 5 `pg-mj-system-biz-*` entries connect to mj-system biz pg also reachable via `mj-system-backend-network`
- `data-agent.llm-provider` (outbound)：`ssh-manager` DGX host entry (192.168.0.189) shares physical host with `local-openai-compat` LLM endpoint

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **A. Single .mcp.json with 13 entries (chosen)** | Single source of truth; easy diff | Long file (~100+ lines) | MCP protocol convention; per-server profiles would be over-engineered |
| B. Per-profile MCP configs | Smaller per-env file | Multiplies maintenance | Rejected — convention is one .mcp.json |
| **C. Wrapper script consolidation (chosen)** | Centralized config; quarterly diff target | One more layer between Claude Code and pg MCP | Necessary — credential mode + URL override + timeout normalization |
| D. 10 distinct pg MCP configs | No wrapper layer | 10× maintenance; can't centrally enforce timeout | Rejected |
| **E. Sentinel defaults for LAN/DEV (chosen)** | Smooth first-clone (no secrets decrypt needed for some tools) | Silent auth-fail | Auth-fail is loud at first use; sentinel format `REPLACE_WITH_*` makes intent clear |
| F. Empty defaults for all | Always force env override | First-clone friction; can't use Claude Code at all | Rejected |
| **G. Fail-loud WAN no-default (chosen)** | Misconfig visible at startup | Slightly worse UX | Correct — WAN tunnels are per-deploy; no sensible default |
| **H. A14 PR gate manual at M1 (chosen)** | No CI infra at M1 | Reviewer must remember | Phase M3 will add `scripts/sdd/check_a14_gate.py` blocking |

## §5 Open Questions

1. **Should REQ-001 cite wrapper's normative behavior explicitly OR treat as side-channel?** Currently `docs/_baselines/pg_server_baseline.md` is the SOR for wrapper behavior; REQ only mentions wrapper file path. Phase M2 decision: pull wrapper contract into REQ-002 OR keep as quarterly-audit reference.

2. **Should REQ explicitly state the fail-loud semantic for WAN entries?** Currently described informally in survey §D.1. Phase M2 decision: codify as REQ-003 OR keep as design intent.

3. **`ssh-manager` 9-host aggregation: count as 1 server or 9?** REQ-001 currently counts as 1 (matches `.mcp.json` entry count); per-host trust posture might require separate enumeration in quarterly audit. Phase M2 decision.

4. **MCP STANDARD `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` not read during survey** (scope: no docs reads). Should REQ-001 wording be re-verified against the STANDARD before authoring? Phase M2 reverify.

> Phase M2 will fill in adapter §BDD Rules + §TDD Rules per `sdd/adapters/claude-code-skill.md`.
