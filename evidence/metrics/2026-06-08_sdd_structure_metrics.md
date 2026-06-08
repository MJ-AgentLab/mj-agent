# SDD Structure Metrics — first report (2026-06-08)

> M6 deliverable (master plan `plans/[PLAN]_spec_anchored_refactor.md` §Phase M6:
> 度量首份报告). First snapshot of the SDD three-pillar structure
> (SDD Kernel + Capability Package + Business Policy) after the M6 cross-cutting
> migration + freeze-refresh + CLAUDE.md slim. **Manual snapshot**; automation
> (a `scripts/sdd/` metrics generator) is a Phase-2 follow-up. Counts are from the
> `develop` tree @ `dc0e511` (post #243); methodology per metric below.

## §1 Capabilities — 5 (4 active / 1 drafting)

| Domain | Capability | lifecycle_state |
|---|---|---|
| data-agent | safe-sql | active |
| data-agent | biz-catalog | active |
| data-agent | llm-provider | active |
| infrastructure | docker-compose | active |
| infrastructure | mcp-server-governance | drafting |

- **Total: 5** (data-agent 3 / infrastructure 2). **4 active**, **1 drafting**
  (mcp-server-governance held per `M4-FU-MCP-GOV-PROMOTION-DEFER`).
- Method: `find capabilities -name spec.yml`; state from each spec's `lifecycle_state`
  (9-state model per `sdd/lifecycle.md`).

## §2 Contracts — 21 artifacts (avg 4.2 / capability)

| Capability | `.contract.yml` | `behavior.feature` | other | total |
|---|---|---|---|---|
| safe-sql | 4 (execute-sql / python / runtime-skill / sql-guardrail) | 1 | — | 5 |
| biz-catalog | 3 (catalog / catalog-db-alignment / runtime-skill) | 1 | — | 4 |
| llm-provider | 3 (prompt / provider / python) | 1 | — | 4 |
| docker-compose | 2 (compose / docker) | 1 | 1 (`runtime.expected.yaml`) | 4 |
| mcp-server-governance | 3 (claude-skill / governance / mcp-server) | 1 | — | 4 |
| **total** | **15** | **5** | **1** | **21** |

- Every capability has exactly 1 `behavior.feature` (BDD spec) + 2-4 declared `.contract.yml`.
- Method: `find capabilities -path '*/contracts/*' -type f`.

## §3 Evidence coverage — 18 files; G8 4/4 active PASS; 5/5 (incl. drafting) carry evidence

| Capability | evidence files | subdirs with content |
|---|---|---|
| safe-sql | 10 | bdd / reports / runtime / security / verification |
| llm-provider | 2 | reports / runtime |
| docker-compose | 2 | reports / runtime |
| mcp-server-governance | 2 | reports / runtime |
| biz-catalog | 1 | runtime |
| **capability-level total** | **17** | |
| infrastructure domain-level | 1 | assessments (X1-relocated git-conventions ASSESSMENT) |

- **G8 (capability-evidence-required)**: 4 active capabilities PASS (≥1 non-`.gitkeep`
  evidence file each); mcp-server-governance is `drafting` → G8 SKIP (but already carries
  2 evidence files). **Coverage = 5/5 (100%) have ≥1 evidence file.**
- Evidence-subdir taxonomy seeded across all 5 (bdd / reports / runtime / tdd /
  verification dirs present; security in 3; assessments at the infra domain level).
- Distribution is uneven (safe-sql 10 vs biz-catalog 1) — expected: safe-sql is the
  most-exercised pilot (L1/L1b/BDD/security audits). Method: `find <cap>/evidence -type f
  ! -name .gitkeep`.

## §4 HITL trigger frequency — canonical 10-enum + observed (M6 #234–#243)

The canonical 10-enum (`policies/ai-agent.md` §4) and observed firings across the M6
doc-governance PRs in the #234–#243 window (excluding 2 dependabot bumps — see caveat).
Counted from the merged PR bodies + their file-stat diffs (`git show` per merge commit):

| Enum | Surface | Observed (#234–#243) |
|---|---|---|
| `mcp-server-trust-posture-change` | `.mcp.json` + infra freeze SKILLs (per `claude-skill.contract.yml hitl_required`) | **2** — X4 #238 (4 infra skills), freeze-refresh #242 (6 infra skills + contract re-freeze) |
| `declared-contract-change` | `capabilities/*/contracts/*` | **2** — X5 #240 (governance + mcp-server contracts), freeze-refresh #242 (claude-skill contract) |
| `bulk-content-purge-or-migration` | archive ceremony / ≥10-file move | **1** — X5 #240 (mcp STANDARD archive ceremony) |
| `sql-guardrail-relax` · `runtime-skill-content-change` · `prompt-version-or-body-change` · `biz-catalog-sync` · `database-migration` · `secrets-grants-or-prod-config` · `ci-blocking-gate-toggle` | (4 in-source 必停 + memory/secrets/CI) | **0** in this window (zero `src/mj_agent/` 必停 + zero `.mcp.json` touched; `ci.yml` saw only a dependabot action-version bump, **not** a `continue-on-error` flip / new gate; G14/G15 flip still held) |
| **procedural HITL** (owner sign-off / decision; not a surface-anchored enum) | AskUserQuestion forks + approvals | **~8** — M6-boundary, xcut-approach, relocates-vs-archives, X5 sign-off, X6「不归档」decision, freeze-refresh auth, M6-next fork, CLAUDE.md-slim pick |

- Read: M6's HITL load was **governance-shaped** (freeze surfaces + contracts + one
  archive) plus owner-decision forks — **zero** data/agent 必停 (guardrail / precheck /
  system.md / SKILL bodies / qcm_catalog) or CI-gate-flip in this window, consistent with a
  docs-governance phase. The 4 in-source 必停 + `ci-blocking-gate-toggle` are the
  highest-stakes triggers and stayed untouched.
- Caveat: this is a **manual** count, not a longitudinal rate. The #234–#243 range nominally
  spans 10 PRs but includes 2 dependabot bumps (#239 GHA + a `setup-uv` action bump) that
  touch no HITL surface — they are excluded from the per-enum counts (the `setup-uv` bump did
  edit `.github/workflows/ci.yml`, but as an action-version bump only, so `ci-blocking-gate-toggle`
  stays 0; the real G11/G12 archive-gate→blocking flip was #233, **outside** this window).
  A scripted HITL-event log (parse PR bodies for declared enums) is the Phase-2 automation target.

## §5 Summary + Phase-2 follow-ups

- **5 capabilities / 21 contracts / 18 evidence files / 5-of-5 evidence coverage** — the
  three-pillar structure is fully populated post-M6.
- Skew to address later: biz-catalog (1) / llm-provider (2) evidence are thin vs safe-sql (10);
  mcp-server-governance promotion drafting→active is held (`M4-FU-MCP-GOV-PROMOTION-DEFER`).
- **Phase-2 metrics automation** (this report's successor): a `scripts/sdd/` generator for
  capability/contract/evidence counts + an HITL-event log parsed from PR bodies, run on a
  cadence; ties into the EVAL framework baseline (also Phase-2 deferred per draft-b Q4).
