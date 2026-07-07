---
type: capability-runbook
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: MCP Server Inventory + Governance

> Phase M1 baseline.

## §1 Startup

MCP servers spawn lazily when Claude Code references them. No explicit startup.

Verify .mcp.json loads correctly:

```bash
# Quick syntax check
uv run python -c "import json; print('servers:', len(json.load(open('.mcp.json'))['mcpServers']))"
# Expected: servers: 14
```

Per spec.yml summary: 14 servers = 1 first-party GitHub + 1 third-party Serena LSP + 10 wrapped pg + 1 third-party ssh-manager + 1 third-party Playwright.

Populate MCP secrets to OS env (one-time per machine per ADR-030):

```powershell
# Decrypts config/secrets-mcp.enc → writes 15 env vars directly to HKCU\Environment
# (Bypasses .env entirely; MCP bundle separate from app secrets bundle)
.\.claude\scripts\setup-mcp-secrets.ps1

# Restart terminal + Claude Code afterwards (env loaded at process start)
```

Per ADR-030 the 15 MCP env vars are:
- 5 SSH passwords (MJ_AGENT_SSH_SERVER_{CLOUD,RUNNER,TEST,PROD,DGX}_PASSWORD)
- 10 PG URL overrides (MJ_AGENT_PG_{MEMORY,BIZ}_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL)

## §2 Health Check

```bash
# Inventory sanity
uv run python -c "
import json
data = json.load(open('.mcp.json'))
servers = data['mcpServers']
assert len(servers) == 14, f'Expected 14 servers, got {len(servers)}'
pg_count = sum(1 for k in servers if k.startswith('pg-'))
assert pg_count == 10, f'Expected 10 pg-* entries, got {pg_count}'
print('OK: 14 servers (10 pg-*)')
"

# Wrapper consistency (REQ-002)
uv run python -c "
import json
data = json.load(open('.mcp.json'))
pg_wrappers = set()
for name, cfg in data['mcpServers'].items():
    if name.startswith('pg-'):
        cmd = cfg.get('command', '')
        pg_wrappers.add(cmd)
assert len(pg_wrappers) == 1, f'Expected 1 wrapper, got {pg_wrappers}'
print(f'OK: all 10 pg-* use same wrapper: {pg_wrappers.pop()}')
"

# Env var presence (after setup-mcp-secrets.ps1)
# Expected: 15 env vars set
echo "MCP env vars status (5 SSH + 10 PG = 15):"
for var in MJ_AGENT_SSH_SERVER_CLOUD_PASSWORD MJ_AGENT_PG_MEMORY_DEV_URL MJ_AGENT_PG_BIZ_DEV_URL; do
  if [ -n "${!var:-}" ]; then echo "  $var: set"; else echo "  $var: MISSING"; fi
done
```

## §3 Troubleshooting

### Symptom: Claude Code MCP server "github" / "serena" / "ssh-manager" failed to start

**Diagnostic**：trust posture issue — third-party server may have upstream regression (Dependabot bumped to broken version) OR env secret missing.

**Resolution**：

- Check env var for the failed server's credential (per `mcp-server.contract.yml`):
  - github: `GITHUB_PERSONAL_ACCESS_TOKEN` set? → `.\.claude\scripts\setup-mcp-secrets.ps1`
  - ssh-manager: 5 `MJ_AGENT_SSH_SERVER_*_PASSWORD` set? → same script
- For third-party servers: check upstream changelog (oraios/serena, iflow-mcp/mcp-ssh-manager)
- If new regression discovered → quarterly audit cycle issue; file `[AGENT]` issue + ADR if trust posture changes

### Symptom: pg-* server fails to connect with `password authentication failed`

**Diagnostic**：URL env override missing OR has stale sentinel.

**Resolution**：

- Verify env override is set:
  - For DEV: `MJ_AGENT_PG_MEMORY_DEV_URL` (default has sentinel)
  - For TEST/PROD LAN: `MJ_AGENT_PG_MEMORY_{TEST,PROD}_LAN_URL` (default has REPLACE_WITH_* sentinel)
  - For WAN: `MJ_AGENT_PG_MEMORY_{TEST,PROD}_WAN_URL` (NO default; required)
- Run `.\.claude\scripts\setup-mcp-secrets.ps1` to populate
- Restart Claude Code (env loaded at process start)

### Symptom: pg-mj-system-biz-* server fails with analyst auth error

**Diagnostic**：upstream analyst role password may have rotated; mj-agent's MCP_PG_BIZ_*_URL env still has old password.

**Resolution**：

- Verify with mj-system owner: latest analyst role password
- Update team-distributed `secrets-mcp.enc` bundle (cross-cap: this capability + infrastructure.secrets-pipeline Phase 2+)
- Re-run `setup-mcp-secrets.ps1`
- Restart Claude Code

### Symptom: Adding a new MCP server in PR fails A14 gate

**Diagnostic**：PR body missing the §4 declaration block.

**Resolution**：

- Add the A14 block to PR body per template in `contracts/governance.contract.yml §a14_pr_gate.pr_body_required_block`
- Block includes: server_name + change_type + trust_posture + credential_mode + rationale
- Reviewer must approve the block before merge
- A14 gate enforcement: Phase M3+ blocking; warning at M1 (per `contracts/behavior.feature` REQ-001)

### Symptom: Wrapper baseline drift detected

**Diagnostic**：community pg MCP upstream changed; `.claude/scripts/pg-server-wrapper.mjs` no longer aligns with `docs/_baselines/pg_server_baseline.md`.

**Resolution**：

- Run quarterly audit task `diff_wrapper_baseline` per `contracts/governance.contract.yml`
- If minor drift (formatting / comments): update baseline doc
- If major drift (API change): file `[AGENT]` issue; coordinate with `infrastructure.secrets-pipeline` (Phase 2+) on wrapper script update
- Either way: A14 PR gate triggers on .claude/scripts/pg-server-* modification

## §4 Related Artifacts

- `contracts/mcp-server.contract.yml` — 14-server inventory + per-entry attributes
- `contracts/governance.contract.yml` — A14 PR gate + quarterly audit process
- `contracts/behavior.feature` — 2 Gherkin scenarios
- ADR-028 — MCP Server Inventory + Governance
- ADR-030 — Secrets Bundle Split (MCP bundle vs app bundle)
- `contracts/governance.contract.yml` — §a14_pr_gate template + §quarterly_audit (former MCP STANDARD §4/§6, archived M6 X5 → `archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_MCP_Server_Governance_v1_0.md`)
- `docs/_baselines/pg_server_baseline.md` — wrapper baseline SOR
- `.claude/scripts/pg-server-start.cmd` + `.claude/scripts/pg-server-wrapper.mjs`
- `.claude/scripts/setup-mcp-secrets.ps1` — env var population (Phase 2+ → secrets-pipeline)
- Cross-cap: `infrastructure.docker-compose` (inbound per spec.yml `cross_capability_refs`; pg-* entries connect to mj-agent-postgres deployed by docker-compose + mj-system biz pg via mj-system-backend-network)
- Cross-cap: `data-agent.llm-provider` (outbound per spec.yml `cross_capability_refs`; ssh-manager DGX-Spark host 192.168.0.189 = local-openai-compat LLM endpoint host)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 silent regression (PR adds MCP server without A14 block; review accepts; trust boundary expanded silently)
- REQ-002 wrapper deviation (one of 10 pg-* uses different wrapper; centralized config broken)
- Quarterly audit lapse > 2 quarters
- Third-party MCP upstream malicious update (supply chain attack); requires immediate `.mcp.json` rollback + ADR

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per `policies/archive.md` retention class permanent.

---

> Phase M1 baseline.
