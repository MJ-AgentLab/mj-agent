# mcp-server-governance Quarterly Audit Q2 2026 (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-5 (**FINAL Stage C unit**)
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: Q2 2026 quarterly audit completed per `governance.contract.yml §6` 4 audit tasks; 13-server inventory verified (1 first-party + 1 third-party LSP + 10 wrapped pg + 1 third-party ssh-manager); ★★★ **11-file cumulative SUT-internal-docstring scope expansion** confirmed via Grep (6 SKILL.md + 4 src/ + .env.example + docker-compose.mj-agent.yml); Stage C cluster closure achieved
- **Cluster**: mcp-server-governance C-5 final Stage C unit; **Stage C cluster (C-1a..C-5) closure summary in §6**

## §1 Goal + Scope

Execute Q2 2026 quarterly audit per `capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml` §6 (4 audit tasks: `re_evaluate_trust_posture` / `diff_wrapper_baseline` / `check_unmaintained_servers` / `check_secret_sentinel_overrides`) against current `.mcp.json` 13-server inventory + `docs/_baselines/pg_server_baseline.md` wrapper baseline + `setup-mcp-secrets.ps1` sentinel patterns + cumulative `.claude/skills/mj-agent-infra-*/` SUT-internal-docstring drift inventory (★★★ 11-file scope per Grep #C5-4).

**C-5 is FINAL Stage C unit** (12th of 12 cumulative); §6 Forward includes Stage C cluster (C-1a..C-5) closure summary + Step 13 user-driven sequence + F-8 post-merge anticipation。 Reuses C-2/C-3/C-4 runtime/ subdir convention precedent (NO YAML frontmatter; H1 + Stage/Branch/Outcome/Cluster bullets; 6 sections) with §3 format: per-audit-task status matrix。

**Out of scope**: live `check_unmaintained_servers` GitHub upstream queries (network actions; SUT-side cannot empirically verify); A14 PR gate live invocation (manual reviewer process); actual baseline diff against community pg MCP repo fetch (requires external repo access; Reference).

## §2 Method

Per-source canonical reference + B-5 micro 微调 minimal anchor:

- **`governance.contract.yml` §6** (canonical contract; 4 audit task definitions verbatim per yaml L51-77): `re_evaluate_trust_posture` (per-server trust posture review) + `diff_wrapper_baseline` (pg_server_baseline.md diff) + `check_unmaintained_servers` (per-server health + last-commit) + `check_secret_sentinel_overrides` (sentinel env var validation)
- **`.mcp.json`** (canonical 必停 surface per memory 9 immutables; 13-server inventory verified): github (1) + serena (2) + 10 pg-* wrapped (5 mj-agent memory dev/test-lan/test-wan/prod-lan/prod-wan + 5 mj-system biz same 5 profiles) + ssh-manager (1; 9 SSH host entries via 5 unique passwords)
- **`docs/_baselines/pg_server_baseline.md`** (canonical baseline; frozen at 2026-05-11): pg-server-{start.cmd,wrapper.mjs} setTypeParser overrides + 4 audit items
- **`docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`** §4 (canonical STANDARD; A14 PR gate template source)
- **`.claude/scripts/setup-mcp-secrets.ps1`** (canonical script; sentinel pattern source for check_secret_sentinel_overrides)
- **B-5 commit `46b0147` runbook** (micro 微调 minimal anchor per Path β / Option b; NO §6 SOPs; §1 +1 trust posture breakdown + §3 +1 14th-server symptom clarifier + §4 +2 cross-cap refs)

Cross-Stage C **11-file SUT-internal-docstring scope** evidence: Grep `.claude/skills/` for `ADR-025` returned 6 SKILL.md files (5 NEW beyond C-3 endpoint-probe per Grep); combined with C-1c execute.py + C-3 llm.py + config.py + endpoint-probe SKILL.md + C-4 .env.example + docker-compose.mj-agent.yml = 11 cumulative source files (per §4.1 documentation per R-2 per-file authoritative ADR target table).

## §3 Results

**Basis: Mixed** (yaml+json+ps1 Empirical via in-process parse + cross-repo Reference for unmaintained checks). Per-audit-task status matrix:

| Audit Task (governance.contract.yml §6) | Current State | Drift Detected | Reconcile Action | Per-row Basis |
|---|---|---|---|---|
| **re_evaluate_trust_posture** | 13-server: 1 first-party (github) + 1 third-party LSP (serena) + 10 first-party-wrapper (pg-mj-agent-memory-5 + pg-mj-system-biz-5; all `.claude\scripts\pg-server-start.cmd`) + 1 third-party (ssh-manager; 9 host entries via 5 unique passwords) | NO new trust posture changes since 2026-05-11; matches spec.yml summary verbatim | None (status quo audit confirmed) | json Empirical |
| **diff_wrapper_baseline** | pg-server-{start.cmd,wrapper.mjs} frozen at 2026-05-11 per `pg_server_baseline.md` L18; setTypeParser(1114/1184) overrides preserved | NO drift (baseline unchanged Q2); upstream `@modelcontextprotocol/server-postgres` version check requires external npm query (Reference) | None empirical (Q2 audit clean); upstream check Reference-pending | text Empirical + Reference (npm) |
| **check_unmaintained_servers** | Per-server last-commit + repo health check requires GitHub API queries (serena: oraios/serena; ssh-manager: iflow-mcp/mcp-ssh-manager; github: anthropic-published) | Cross-repo limitation; SUT-side cannot empirically verify | Out-of-scope this audit; future automation per Phase M3+ governance.contract.yml TBD | Reference (cross-repo network actions out-of-scope) |
| **check_secret_sentinel_overrides** | `setup-mcp-secrets.ps1` populates 15 env vars (5 SSH passwords + 10 PG URL overrides per ADR-030 secrets bundle split); sentinel pattern: 6 with `:-default` fallback + 4 WAN URL required-no-fallback (per `.mcp.json` L27/36/45/54/63/73/81/90/99/108 inventory) | NO drift in sentinel patterns; .mcp.json `${VAR:-default}` ↔ setup-mcp-secrets.ps1 alignment verified at yaml parse + ps1 source | None (baseline compliance confirmed) | ps1+json Empirical |

Per-row aggregate: 3 of 4 audit tasks Empirical-verifiable (trust posture + baseline diff + sentinel overrides); 1 task (unmaintained_servers) requires cross-repo Reference (parallel to C-1c L4 cross-repo + C-3 endpoint empirical limitations). Q2 audit overall outcome: **NO new drifts detected within SUT-scope** for 4 audit tasks; cross-repo audit deferred to future automation per governance.contract.yml §6 TBD M3+.

## §4 Observations

### §4.1 ★★★ 11-File SUT-Internal-Docstring Scope Expansion (Per Grep #C5-4; Cumulative C-1c + C-3 + C-4 + C-5)

Grep `.claude/skills/` for `ADR-025` (Step 1 finalize) returned **6 SKILL.md files** (5 NEW beyond C-3 endpoint-probe known); combined with prior cumulative Stage C drift inventory yields **11 source files** referencing archived ADR-025 (per PR-Γ 2026-05-11 split into ADR-026/027/028)。Per-file authoritative ADR target mapping:

| # | File:Line | Verbatim ADR-025 Reference | Authoritative Target | Surface Source |
|---|---|---|---|---|
| 1 | `src/mj_agent/tools/sql/execute.py` L4-15 | (2-layer numbering "1./2./3." vs 4-layer L1/L1b/L3/L4) | per-spec.yml + behavior.feature 4-layer (ADR-029 middleware context) | C-1c §4.1 |
| 2 | `src/mj_agent/llm.py` L3 | "ADR-025" module docstring | **ADR-027** (LLM Provider Abstraction) | C-3 §4.1 |
| 3 | `src/mj_agent/config.py` L62 | "...ADR-025" inline comment | **ADR-027** | C-3 §4.1 |
| 4 | `.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` L10+L184 | "ADR-025 / PR-2 of multi-env+DGX+MCP bundle" | **ADR-027** (PR-2 = LLM provider) | C-3 §4.1 |
| 5 | `.env.example` L54 | "...ADR-025" LLM Provider section | **ADR-027** | C-4 §4.2 |
| 6 | `infra/docker/docker-compose.mj-agent.yml` L2 | "ADR-008 + ADR-025" header | ADR-008 + **ADR-026** (PR-1 multi-env compose) | C-4 §4.1 |
| 7 | `.claude/skills/mj-agent-infra-storage-stack/SKILL.md` L220+L230 | "Profile 注解（ADR-025）" + "ADR-025 §D.2 DGX-mode" | **ADR-026** (multi-env profile) + **ADR-027** (DGX/LLM context) | ★ C-5 §4.1 NEW |
| 8 | `.claude/skills/mj-agent-infra-studio-probe/SKILL.md` L38 | "Step 0 — LLM endpoint pre-check (PR-2 / ADR-025)" | **ADR-027** (PR-2 LLM) | ★ C-5 §4.1 NEW |
| 9 | `.claude/skills/mj-agent-infra-docker-compose/SKILL.md` L119 | "§Profile Matrix (PR-1 / ADR-025 4-file 分层)" | **ADR-026** (PR-1 multi-env compose) | ★ C-5 §4.1 NEW |
| 10 | `.claude/skills/mj-agent-infra-env-setup/SKILL.md` L103+L107+L117 | "PR-2 / ADR-025" (LLM L103+L117) + "PR-3 / ADR-025" (SSH passwords L107) | **ADR-027** (PR-2 LLM) + **ADR-028** (PR-3 MCP) per-line | ★ C-5 §4.1 NEW |
| 11 | `.claude/skills/mj-agent-infra-env-teardown/SKILL.md` L20+L45+L146 | "PR-1 / ADR-025 4-file 分层" + wikilink to archived `[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction` | **ADR-026** (PR-1 multi-env) + wikilink target archive path | ★ C-5 §4.1 NEW |

**Sub-type repeat rate**: 4 units / 7 = **57%** (C-1c + C-3 + C-4 + C-5; leading drift sub-type)。**Systematic ADR archive ceremony lag pattern** across `.claude/skills/mj-agent-infra-*/` SKILL family + src/ + canonical infra YAML + env template — spec-anchored discipline locks spec/behavior/runbook (governed under PR review + freeze contracts) but in-source documentation + SKILL descriptions + env templates lag behind ADR archive ceremonies (PR-Γ 2026-05-11 split was last touch on ADR-025; subsequent updates didn't propagate).

**Disposition** (per C-1c + C-3 + C-4 §4.1 cumulative precedent): F-7 cluster amend observation candidate; **NOT new M4-FU entry** (orthogonal to existing 6 M4-FU registry; consistent with cumulative SUT-internal-docstring sub-type disposition); **NOT modified in C-5** (batch boundary 守约: 不动 6 SKILL.md + .env.example + docker-compose.yml + 4 src/ within current batch). **Reconcile path scope expanded: post-M4-BC small docs PR scope = 11-file edit** (was 4-file post-C-4); ~11-15 lines change across 11 files (per-file 1-3 line edit per R-2 authoritative ADR target table). **F-7 cluster amend governance recommendation**: implement **docstring drift detector** (类 C-2 4-mechanism governance maturity template OR `scripts/diff_biz_schema.py` pattern; scope = source code module docstrings + SKILL.md frontmatter + canonical YAML/env templates references) to systematically catch ADR archive ceremony lag at PR review time.

### §4.2 B-5 Micro 微调 Anchor Confirmation

B-5 commit `46b0147` Path β / Option (b) micro 微调 minimal anchor (+5 lines net: §1 +1 trust posture breakdown + §3 +1 14th-server Phase M3+ blocking clarifier + §4 +2 cross-cap refs)。C-5 cross-refs go DIRECTLY to canonical (per C-3 B-3 minimal pattern; vs C-4 B-4 SOP rich intermediate layer). Audit per §6 4 tasks confirms B-5 micro 微调 wording alignment with `.mcp.json` 13-server reality + governance.contract.yml §6 task definitions — no B-5 specific drift surfaced post-landing。

### §4.3 Cross-Repo Audit Limitation (check_unmaintained_servers per R-C5-6)

`check_unmaintained_servers` audit task (governance.contract.yml §6 L67-71) requires external GitHub API queries (per-server last-commit date + repo health). SUT-side mj-agent cannot empirically verify within this evidence file; basis for §3 row = **Reference (cross-repo network actions)**. Full empirical verification requires (a) live GitHub API queries OR (b) Phase M3 BDD test landing per behavior.feature L<NN> @meta-gate:A14 (TBD).

Parallel to **C-3 endpoint empirical limitation** (LLM endpoint network actions) + **C-1c §4 L4 cross-repo reference-contract limitation** (R__analyst_permissions.sql lives in mj-system repo)。

### §4.4 Stage C Cluster (C-1a..C-5) Closure Summary

**7 units, 4 subdirs, 7 distinct §3 schemas, 7 distinct §4 epistemic findings**:

- C-1a (verification/ 80 lines per-keyword) — SUT-spec UNDOCUMENTED drift
- C-1b (verification/ 95 lines per-rule-ID) — SUT-runbook UNDOCUMENTED drift (10× magnitude)
- C-1c (security/ 116 lines attack-vector × layer matrix) — SUT-internal-docstring UNDOCUMENTED (1st sub-type; execute.py L4-15)
- C-2 (runtime/ 96 lines per-source freshness) — DOCUMENTED-drift positive null (governance maturity break)
- C-3 (runtime/ 98 lines per-REQ probe) — SUT-internal-docstring UNDOCUMENTED (2nd; 3-file scope at C-3 time)
- C-4 (runtime/ 108 lines per-service smoke matrix) — SUT-internal-docstring UNDOCUMENTED (3rd; 1 NEW + 1 cross-cap C-3 expansion to 4-file)
- **C-5 (runtime/ this file per-audit-task matrix) — SUT-internal-docstring UNDOCUMENTED (4th; 5 NEW SKILL.md via Grep; cumulative 11-file scope)**

**Aggregate metrics**:
- §0 substantive surfacing rate: **7/7 = 100%** (Stage C); Stage B→C cumulative 11/11 = 100% (all post-Stage A units null-positive but always with substantive intercepts)
- UNDOCUMENTED drift rate: 5/7 = **71%** (Stage C); 1 documented-positive-null + 1 critical path correction
- SUT-internal-docstring sub-type repeat rate: 4/7 = **57%** (leading sub-type; F-7 docstring drift detector candidate)
- Cumulative SUT-internal-docstring scope: **11 source files** (Phase F-7 reconcile path)
- §7 episodes Stage C: 6+5+5+5+5+7+~5 = ~38 (final Stage C tally; aggregate Stage A 19 + Stage B 24 + Stage C ~38 = ~81 cumulative for F-7 cluster amend)

## §5 Cross-references

- `capabilities/infrastructure/mcp-server-governance/spec.yml` REQ-001 (13-server inventory + A14 PR gate per §4 template) / REQ-002 (10 pg-* same wrapper)
- `capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml` §6 4 audit tasks verbatim (re_evaluate_trust_posture / diff_wrapper_baseline / check_unmaintained_servers / check_secret_sentinel_overrides; per L51-77)
- `capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature` 2 BDD scenarios `@meta-gate:A14`
- **B-5 commit `46b0147` runbook** (Path β micro 微调; §1 +1 trust posture breakdown + §3 +1 14th-server Phase M3+ blocking clarifier + §4 +2 cross-cap refs to docker-compose + llm-provider per spec.yml `cross_capability_refs`)
- **`.mcp.json` 13-server inventory**: 1 github (first-party) + 1 serena (third-party LSP) + 10 wrapped pg-* (5 mj-agent-memory dev/test-lan/test-wan/prod-lan/prod-wan + 5 mj-system-biz same 5 profiles; all `.claude\scripts\pg-server-start.cmd`) + 1 ssh-manager (third-party; 9 SSH host entries via 5 unique passwords per env: cloud + runner-lan/wan + test-lan/wan + prod-lan/wan + dgx-lan/wan)
- `docs/_baselines/pg_server_baseline.md` (canonical baseline; frozen at 2026-05-11; pg-server-{start.cmd,wrapper.mjs} setTypeParser(1114/1184) overrides)
- `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` §4 (A14 PR gate template source)
- `.claude/scripts/setup-mcp-secrets.ps1` (sentinel pattern source per ADR-030 secrets bundle split; 5 SSH + 10 PG URL = 15 env vars)
- **6 SKILL.md files referencing ADR-025** (per Grep #C5-4; F-7 reconcile target list per §4.1 per-file table):
  - `mj-agent-infra-llm-endpoint-probe/SKILL.md` (per C-3 §4.1; → ADR-027)
  - `mj-agent-infra-storage-stack/SKILL.md` (★ NEW; → ADR-026 + ADR-027 per-line)
  - `mj-agent-infra-studio-probe/SKILL.md` (★ NEW; → ADR-027)
  - `mj-agent-infra-docker-compose/SKILL.md` (★ NEW; → ADR-026)
  - `mj-agent-infra-env-setup/SKILL.md` (★ NEW; → ADR-027 + ADR-028 per-line)
  - `mj-agent-infra-env-teardown/SKILL.md` (★ NEW; → ADR-026)
- Authoritative ADR active set: **ADR-026** (Multi-Env Compose) + **ADR-027** (LLM Provider) + **ADR-028** (MCP Governance) + ADR-029 (Tool Error Middleware) — per PR-Γ 2026-05-11 split from archived ADR-025
- Archived ADR-025 historical reference (`archive/decisions/superseded/[DEPRECATED]_[ADR]_025_*.md`; relocated from docs/archive/adr/ in M5-PR3b; wikilink target file path persists post-archive per archive ceremony retention)
- C-3 evidence `runtime/2026-05-23_endpoint_probe.md` §4.1 (originally 3-file scope; now 4-file post-C-4 expansion; 11-file post-C-5 expansion)
- C-4 evidence `runtime/2026-05-23_compose_smoke.md` §4.1 (docker-compose.mj-agent.yml L2 ADR-025 → ADR-026) + §4.2 (.env.example L54 cross-cap C-3 expansion)

## §6 Forward

### §6.1 Stage C Cluster (C-1a..C-5) Closure Summary

**7 units complete; 4 subdirs (verification/ + security/ + runtime/ × 4 files); 7 distinct §3 schemas (per-keyword / per-rule-ID / matrix / per-source / per-REQ / per-service / per-audit-task); 7 distinct §4 epistemic findings (4 UNDOCUMENTED SUT drifts + 1 documented-positive-null + 1 critical path correction + 1 cumulative 11-file scope expansion)**。

Cumulative metrics (final Stage C tally):
- §0 substantive surfacing rate: 7/7 = 100% (Stage C); Stage B→C cumulative 11/11
- UNDOCUMENTED drift rate: 5/7 = 71% (Stage C)
- SUT-internal-docstring sub-type: 4/7 = 57% leading; **cumulative 11-file scope**
- §7 episodes: ~81 cumulative (Stage A 19 + Stage B 24 + Stage C ~38)
- F-7 cluster amend governance recommendation: docstring drift detector candidate template
- F-7 reconcile path scope: 11-file edit post-M4-BC small docs PR

### §6.2 Step 13 User-Driven Action Sequence (m4-bc 累计 12 Commits)

Stage C close achieved with C-5 commit (12th of 12)。Next:
- `/mj-agent-git-push` → push `documentation/spec-anchored-refactor-m4-bc` to origin + gitee (双 push 双仓)
- `/mj-agent-git-pr` → open **PR #M4-BC** targeting `develop`
- PR title: `docs(stage-bc): Phase M4 Stage B+C — 5 runbook gap-fill + 7 evidence files`
- PR body: per-commit table + Stage C cluster closure summary + 11-file F-7 reconcile path note + cumulative §7 episodes count

### §6.3 F-8 Post-Merge Anticipation + Phase M4 Stage D 起步

PR #M4-BC merge → F-8 post-merge skill (10 steps) propagates:
- Stage B+C close → master plan `[PLAN]_spec_anchored_refactor.md` `phase_progress` field update
- **Action 2 master plan small docs PR** (6 M4-FU registry entries cumulative capture: BODY-SHA256-DOCSTRING-CLARIFY + V4-MODE-B-CLEANUP + BODY-SHA256-CANONICAL-REFACTOR + V4-MODE-B-IMPL + A2-HOOK-IMPROVER-BODY-M5-DEFER + OUTLINE-STAGE-B-WORDING-REFRAME)
- **F-7 cluster amend trajectory note** (~81 §7 episodes + 11-file docstring drift reconcile candidate)

Phase M4 Stage D 起步 (G8 evidence-required + G19-G22 BDD blocking; new worktree `documentation/spec-anchored-refactor-m4-d`); Stage E-F (TDD warning + EVAL placeholders + F-7/F-8 closure; F-6 dropped per A-3 R-2 verdict)。
