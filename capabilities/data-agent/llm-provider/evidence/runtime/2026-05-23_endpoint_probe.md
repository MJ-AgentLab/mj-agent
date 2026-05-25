# llm-provider Endpoint Probe (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-3
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: REQ-001/002/003 probe verification basis = **Conceptual-Mostly** (ZERO existing unit tests per spec.yml L22-23 + behavior.feature L58); 1 §4.1 SUT-internal-docstring drift surfaced **3-file scope** (llm.py:3 + config.py:62 + endpoint-probe SKILL.md:3+10 all reference archived ADR-025 instead of authoritative ADR-027); runtime/ subdir created implicitly (FIRST file in llm-provider/evidence/runtime/)
- **Cluster**: llm-provider C-3 per-capability runtime check; **2nd file in runtime/ subdir overall** (after C-2 biz-catalog)

## §1 Goal + Scope

Verify llm-provider endpoint probe path per `spec.yml` REQ-001 (ark provider LLMConfigError) + REQ-002 (local-openai-compat no extra_body.thinking) + REQ-003 (effective_llm_api_key EMPTY sentinel + LLM_PROVIDER validation + mj-agent check provider-aware). C-3 reuses C-2 `runtime/` subdir convention precedent (NO YAML frontmatter; H1 + Stage/Branch/Outcome/Cluster bullets; 6 sections) with §3 format adjustment: per-REQ probe status report (vs C-2 per-source freshness table). **B-3 anchor minimal** (commit `25c6c99` frontmatter-only edit; NO §6 SOP intermediate layer per Path β/Option b) — C-3 cross-refs go DIRECT to canonical spec.yml + behavior.feature + src/mj_agent/{llm,config,cli}.py + endpoint-probe SKILL.

**Out of scope**: live endpoint hit verification (network actions require live DGX/Ark endpoint OR Phase M3 BDD test landing per behavior.feature L57); REQ-005 envelope schema (orthogonal); deployment of LLM serving containers (per SKILL.md "MUST NOT use for" — out of mj-agent governance).

## §2 Method

Per-source canonical implementation + skill reference:

- **`src/mj_agent/llm.py::make_llm()`** (L32-87; canonical 必停 surface): ark branch L43-67 (extra_body.thinking from llm_thinking_enabled); local-openai-compat branch L69-87 (NO extra_body); LLMConfigError class L28; provider-specific credential validation lazy (call-time, not Settings construction)
- **`src/mj_agent/config.py::Settings`** (L23+; pydantic-settings; canonical): `llm_provider: Literal["ark", "local-openai-compat"]` L69 + provider-aware effective_llm_base_url / effective_llm_api_key cached_properties + EMPTY sentinel handling per REQ-003
- **`src/mj_agent/server/cli.py::check()`** (L64+; canonical; mj-agent check entry): provider-aware credential validation; non-zero exit + reason on stderr; suitable for Docker HEALTHCHECK (per Phase 1 sub 1.H)
- **`/mj-agent-infra-llm-endpoint-probe` SKILL** (canonical SKILL; A-1 amended; black-box reference): 3-step probe (Step 0 .env pre-check + Step 1 /v1/models + Step 2 1-token chat smoke + Ollama /api/tags fallback)

Empirical run protocol per behavior.feature scenarios: `uv run mj-agent check` (provider-aware credential validation) → if `LLM_PROVIDER=local-openai-compat` → `/mj-agent-infra-llm-endpoint-probe` SKILL execution → live endpoint reachability + model id match + 1-token smoke。No automation gates fire at Phase M1 (per behavior.feature L57: "Phase M3 lands tests/bdd/data_agent/llm_provider/steps/").

## §3 Results

**Basis: Conceptual-Mostly** (per `tests/unit/` baseline = ZERO tests for llm or config modules per spec.yml L22-23 + behavior.feature L58 + Bash `ls tests/unit/ | grep -iE "llm|config"` returned empty). Full empirical requires (a) Phase M3 BDD test landing OR (b) live LLM endpoint hit via `mj-agent check` command execution. Per-REQ probe outcome status report:

| REQ ID | Probe Description | Canonical Source | Verification Status | Per-REQ Basis |
|---|---|---|---|---|
| **REQ-001** | Ark provider LLMConfigError when both ARK_API_KEY + LLM_API_KEY empty | `llm.py` L43-67 ark branch + L46-50 LLMConfigError raise | Conceptual: source review confirms error message contains ARK_API_KEY + setup-env.ps1 hint + LLM_API_KEY fallback wording per REQ-001 BDD scenario | Conceptual (no unit test; Phase M3 BDD pending) |
| **REQ-002** | Local provider constructs ChatOpenAI WITHOUT extra_body.thinking | `llm.py` L78-87 local-openai-compat branch (NO extra_body kwarg per L85-86 comment) | Conceptual: source review confirms ChatOpenAI construction omits extra_body; comment explicitly notes vLLM/SGLang/Ollama incompatibility | Conceptual (no unit test) |
| **REQ-003** | effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY empty | `config.py` Settings (effective_llm_api_key cached_property; "EMPTY" sentinel per REQ-003 BDD L51) | Conceptual: source review pending full config.py read (Step 1 preview confirmed Settings class L23+ + llm_provider L69 Literal validation) | Conceptual (no unit test) |
| **mj-agent check** | Provider-aware credential validation; non-zero exit on failure | `cli.py` L64+ check() command | Partial Empirical: command exists + can be invoked manually; output format per spec.yml REQ-003 ("llm provider = <name> (endpoint=<url>)") | Partial (manual invocation possible; no automation) |
| **Live endpoint** | /v1/models reachability + model id match + 1-token chat smoke | `/mj-agent-infra-llm-endpoint-probe` SKILL (3-step probe) | Reference-Conceptual: SKILL execution requires live DGX/Ark endpoint + analyst-side network access | Reference (network-gated; out of mj-agent SUT empirical scope) |

Per-row aggregate: REQ-001/002/003 rows Conceptual (no unit tests); mj-agent check row Partial Empirical (manual invocation); Live endpoint row Reference-Conceptual (network limitation per C-1c L4 reference-contract parallel).

## §4 Observations

### §4.1 SUT-Internal-Docstring Drift (#C3-4; 4th UNDOCUMENTED; 2nd SUT-internal-docstring sub-type repeat; **3-File Scope**)

3-source authoritative-vs-outlier triangulation:

- **Authoritative**: `spec.yml` `related_decisions` lists `docs/adr/[ADR]_027_LLM_Provider_Abstraction.md`; `behavior.feature` L21/L33/L46 `@adr:ADR-027` tags; CLAUDE.md confirms ADR-027 active + ADR-025 archived in PR-Γ 2026-05-11 (split into ADR-026 Multi-Env Compose / ADR-027 LLM Provider Abstraction / ADR-028 MCP Server Governance)
- **Outlier 3-file scope** (broader than initially identified):
  1. `src/mj_agent/llm.py` L3 module docstring: "mj-agent supports two providers (selected by `LLM_PROVIDER` env, ADR-025)"
  2. `src/mj_agent/config.py` L62 inline comment: "# ── 2. LLM Provider (multi-provider abstraction; ADR-025) ─────────"
  3. `.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` L3+L10: "ADR-025 / PR-2 of multi-env+DGX+MCP bundle" (historically accurate pre-split reference; doesn't update to ADR-027 post-split)

**3 source files reference archived ADR-025** instead of authoritative ADR-027. Sub-type pattern: 2nd SUT-internal-docstring UNDOCUMENTED drift cumulative (after C-1c §4.1 execute.py L4-15 2-layer vs 4-layer naming); **sub-type repeat rate: 2/5 = 40%** (leading drift sub-type across Stage C; spec-anchored discipline locks spec/behavior/runbook but in-source docstrings + SKILL descriptions lag behind ADR archive ceremonies).

**Disposition** (per C-1c §4.1 cumulative precedent): F-7 cluster amend observation candidate; **NOT new M4-FU entry** (orthogonal to existing 6 registry candidates; consistent with cumulative §4.1 disposition); **NOT modified in C-3** (batch boundary 守约: 不动 llm.py + config.py + SKILL.md canonical surfaces). Reconcile path: Phase F-7 closure cumulative amend OR independent post-M4-BC small docs PR — **3-file edit** (llm.py L3 + config.py L62 + endpoint-probe SKILL.md L3+L10 all `ADR-025` → `ADR-027`).

### §4.2 ZERO Unit Tests Gap Acknowledgment

Per `spec.yml` L22-23 ("**ZERO existing unit tests** (gap) — all BDD scenarios drive new test code in Phase M3") + `behavior.feature` L58 ("Existing automation: NONE — survey §B.4 confirmed zero unit tests touch make_llm / LLMConfigError / effective_*"). Bash `ls tests/unit/` confirms no `test_llm*.py` or `test_config*.py` files exist.

**This is acknowledged Phase M1 baseline state**, not C-3 fault. Phase M3 BDD test landing per behavior.feature L57 (`tests/bdd/data_agent/llm_provider/steps/`) is the empirical path. C-3 evidence file documents current Phase M1 status; subsequent Phase M3 commit will land BDD tests + flip §3 basis from Conceptual-Mostly to Empirical.

### §4.3 Endpoint Empirical Limitation (Per C-1c L4 Reference-Contract Parallel)

Endpoint probe is fundamentally a network action — requires live DGX-Spark endpoint (192.168.0.189) OR live Ark endpoint (ark.cn-beijing.volces.com) OR Ollama local endpoint. mj-agent SUT-side cannot empirically verify endpoint reachability without live external system access.

Parallel to **C-1c §4 cross-repo limitation** (L4 GRANT + statement_timeout lives in mj-system R__analyst_permissions.sql; SUT-side reference-contract only). C-3 §3 "Live endpoint" row basis = **Reference-Conceptual**; `/mj-agent-infra-llm-endpoint-probe` SKILL execution is the path when live verification needed (operator-invoked per SKILL "MUST run when" triggers; not automated).

## §5 Cross-references

- `capabilities/data-agent/llm-provider/spec.yml` — REQ-001 (ark) / REQ-002 (local-openai-compat) / REQ-003 (LLM_PROVIDER validation + EMPTY sentinel); spec.yml L22-23 ZERO unit tests acknowledgment
- `capabilities/data-agent/llm-provider/contracts/behavior.feature` 3 BDD scenarios (L21/L33/L46 `@adr:ADR-027` tags; L57 Phase M3 test landing + L58 ZERO existing automation note)
- `capabilities/data-agent/llm-provider/runbook.md` (B-3 commit `25c6c99` frontmatter-only edit; **minimal anchor; NO §6 SOP intermediate layer per Path β/Option b**)
- `src/mj_agent/llm.py`:
  - L3 module docstring (★ ADR-025 archived reference per §4.1 drift; should be ADR-027)
  - L28 LLMConfigError class
  - L32-87 make_llm() factory (ark+local branches)
- `src/mj_agent/config.py`:
  - L23+ Settings (pydantic-settings)
  - L62 inline comment (★ ADR-025 archived reference per §4.1 drift; should be ADR-027)
  - L69 llm_provider Literal validation
  - effective_llm_api_key cached_property (EMPTY sentinel per REQ-003)
- `src/mj_agent/server/cli.py` L64+ check() command (provider-aware credential validation)
- `.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` (canonical SKILL; A-1 amended):
  - L3+L10 (★ ADR-025 archived reference per §4.1 drift; should be ADR-027)
  - 3-step probe Workflow (Step 0 pre-check + Step 1 /v1/models + Step 2 1-token chat smoke)
- `docs/adr/[ADR]_027_LLM_Provider_Abstraction.md` (**authoritative** active decision record per PR-Γ 2026-05-11 split)
- `docs/archive/adr/[DEPRECATED]_[ADR]_025_*.md` (historical reference; archived per PR-Γ; cited in §5 as drift context only)
- `policies/ai-agent.md §4` — canonical 10-enum (NOT triggered for C-3; documented for batch boundary discipline)

## §6 Forward

This evidence file (C-3) is the **2nd per-capability runtime/ evidence** (after C-2 biz-catalog):

- **C-2** (`biz-catalog/evidence/runtime/2026-05-23_freshness_check.md`; 96 lines; commit `cf674a9`) — biz-catalog freshness check; documented-drift-only positive null
- **C-3** (this file) — llm-provider endpoint probe; runtime/ subdir created implicitly; 5th drift surface (4th UNDOCUMENTED; 2nd SUT-internal-docstring sub-type; 3-file scope)
- **C-4** (next) — docker-compose smoke evidence; `evidence/runtime/2026-05-23_compose_smoke.md`; ~100-150 lines; B-4 commit `c8f37d6` §6.1+§6.2 SOPs anchor (full SOP intermediate layer)
- **C-5** — mcp-server-governance Q2 audit evidence; `evidence/runtime/2026-05-23_quarterly_audit_q2.md`; ~120-180 lines; B-5 commit `46b0147` §1+§3+§4 micro 微调 anchor; **FINAL Stage C unit**

Stage C close → m4-bc 累计 12 commits → user-driven Step 13 (push + PR #M4-BC targeting develop)。Cumulative 5 distinct epistemic findings (C-1a SUT-spec / C-1b SUT-runbook / C-1c SUT-internal-docstring / C-2 documented-drift-only pattern break / C-3 SUT-internal-docstring 3-file expanded scope) feed F-7 cluster amend governance maturity insight + **docstring drift detector candidate template per 40% sub-type repeat rate**。
