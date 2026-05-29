---
type: sdd-kernel
artifact: gates
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# SDD CI Gates

> Phase M0 skeleton — G1-G17 全局 + 8 stack-specific + G19-G28 BDD/TDD = ~33 gate 终态.
> Phase M0 仅启用 G1/G2/G9 **warning mode**（per `.github/workflows/ci.yml`）.
> 完整 gate 矩阵 + 启用策略在 Phase M2-M6 内容填充.

## §1 全局 Gate（G1-G17）

| Gate | 脚本 | 含义 | 启用 Phase | 阻塞模式 |
|---|---|---|---|---|
| G1 | `scripts/sdd/check_capability_schema.py` | spec.yml schema 合规 | M0 warning / M2 blocking | warning |
| G2 | `scripts/sdd/check_traceability.py` | trace.yml REQ→BDD→CONTRACT→TEST 链路完整 | M0 warning / M3 blocking | warning |
| G3 | `scripts/sdd/check_contracts.py` | contracts/ 非空 + 格式（含 behavior.feature 存在性，高风险）| M1 warning / M3 blocking | TBD M3 |
| G4 | `scripts/sdd/check_plan_vs_diff.py` | PR scope 与 plan 漂移 | M3 blocking | TBD M3 |
| G5 | `scripts/sdd/check_traceability.py`（trace.yml）| trace.yml schema 合规 | M1 warning / M2 blocking | TBD M2 |
| G6 | （内置 §"mj-agent specific hard stops"）| 4 项专属必停拦截 | M0 enforced via guard-git-workflow.ps1 + SKILL anti-patterns | enforced |
| G7 | `scripts/sdd/check_secret_exposure.py` | secrets.enc / secrets-mcp.enc 不入 image / git | M2 blocking | TBD M2 |
| G8 | （evidence required）| capability `state: active` 后 evidence/ 至少 1 文件 | M4 blocking | TBD M4 |
| G9 | `scripts/sdd/generate_index.py` | capabilities/INDEX.md auto-gen | M0 warning | warning |
| G10 | reserved | — | — | — |
| G11 | `scripts/sdd/check_archive_manifest.py` | archive.yml + ai_visibility 必填 | M5 blocking | TBD M5 |
| G12 | `scripts/sdd/check_archive_manifest.py` | 同上 | M5 blocking | TBD M5 |
| G13 | reserved | — | — | — |
| G14 | `scripts/sdd/check_archived_references.py` | active 文件不引用 archived 路径 | M5 blocking | TBD M5 |
| G15 | 同 G14 | — | M5 blocking | TBD M5 |
| G16 | reserved | — | — | — |
| G17 | reserved（archive ai_visibility）| — | M5 blocking | TBD M5 |

## §2 Stack-Specific Gate（8 adapter gate；Phase M2-M3）

| Gate | 脚本 | Adapter | 启用 Phase |
|---|---|---|---|
| Python | `scripts/sdd/check_python_contracts.py` | python.contract.yml | M2 warning / M3 blocking |
| Agent | `scripts/sdd/check_agent_contracts.py` | agent.contract.yml | M2 warning / M3 blocking |
| Prompt | `scripts/sdd/check_prompt_contracts.py` | prompt.contract.yml | M2 warning / M3 blocking |
| Claude-Skill | `scripts/sdd/check_claude_skill_contracts.py` | claude-skill.contract.yml | M2 warning / M3 blocking |
| Docker | `scripts/sdd/check_docker_contracts.py` | docker / compose.contract.yml | M2 warning / M3 blocking |
| Runtime-Expected | `scripts/sdd/check_runtime_expected.py` | runtime.expected.yaml | M3 |
| docker-bdd-scenario-check | `scripts/sdd/check_bdd_scenario_trace.py`（Docker 子集）| docker behavior.feature | M3 warning / M4 blocking |
| docker-tdd-contract-test | `scripts/sdd/check_tdd_refactor_contract.py`（Docker 子集）| docker contract change | M3 blocking |

## §3 BDD/TDD Gate（G19-G28；Phase M3-M6）

| Gate | 脚本 | 含义 | 启用 Phase |
|---|---|---|---|
| G19 | `scripts/sdd/check_bdd_scenario_trace.py` | 关键 scenario 绑定 REQ/CTR | M3 warning / M4 blocking |
| G20 | `scripts/sdd/check_bdd_step_coverage.py` | 自动化 scenario 有 step definition；step 覆盖率达标 | M3 warning |
| G21 | `scripts/sdd/check_bdd_acceptance.py` | `@risk:critical\|high` 验收场景通过率（`pass_rate: 1.0`）或 runbook.md justification fallback（同 G22，per L121） | M4 |
| G22 | `scripts/sdd/check_bdd_unautomated.py` | 未自动化 scenario 在 runbook 说明原因 | M4 |
| G23 | `scripts/sdd/check_tdd_test_list.py` | 高风险 task 有 tdd.test_list | M4 warning / M6 blocking |
| G24 | 同 G23（bugfix-regression）| bugfix PR 必有 regression test | M4 blocking |
| G25 | 同 G23（changed-code-has-test）| 改动 Python 代码必有对应测试 | M4 |
| G26 | 同 G23（red-green-evidence）| 高风险 task evidence/tdd/ 有 red+green | M6（per R-G19 缓解，AI 代码场景下软要求）|
| G27 | `scripts/sdd/check_tdd_refactor_contract.py` | refactor PR 行为测试不变 | M6 |
| G28 | 同 G27（contract-test-first）| contract 变更必须有 failing test 证据 | M3 blocking（严格执行；per R-G19）|

## §4 mj-agent specific hard stops（4 项 in-source 专属必停；canonical enum subset）

以下 in-source 文件任何变更**永久 manual blocking**（不可绕过；不在 CI gate 自动化覆盖范围 — 由
`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook + 各 runtime SKILL anti-patterns 段
+ A12 description gate + HITL 强制人审）. 这 4 项是 `policies/ai-agent.md §4 HITL Required
Scenarios — Canonical 10-Enum` 的 in-source 子集（前 4 行）：

| Hard Stop Enum | 路径 | 工作流 |
|---|---|---|
| `sql-guardrail-relax` | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | `sdd/workflows/cross-capability-change.md`（safe-sql 跨 4 层影响）|
| `runtime-skill-content-change` | `src/mj_agent/skills/*/SKILL.md` body | `mj-agent-runtime-skill-doc-improve` skill（read-only 提议 diff）|
| `prompt-version-or-body-change` | `src/mj_agent/prompts/system.md` version 或 body | `mj-agent-runtime-prompt-version-bump` skill（含义吸收原 `prompt-version-bump` + body 行为边界变更）|
| `biz-catalog-sync` | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | `mj-agent-runtime-biz-catalog-sync` skill |

> 4 项必停的细化触发条件 + HITL 模板见 `policies/data-boundary.md` §"4 项专属必停" 段.
> 其余 6 项 HITL canonical enum（`mcp-server-trust-posture-change` / `declared-contract-change`
> / `database-migration` / `secrets-grants-or-prod-config` / `ci-blocking-gate-toggle` /
> `bulk-content-purge-or-migration`）见 `policies/ai-agent.md §4`.

## §5 Gate 启用策略

| 阶段 | 策略 |
|---|---|
| Phase M0 | G1 / G2 / G9 **warning-only**；其余未启用 |
| Phase M1 | G3 / G5 warning |
| Phase M2 | G1 / G2 / G5 → blocking；G7 启用 blocking；8 adapter gate warning |
| Phase M3 | adapter gate → blocking；G19 / G20 warning；G28 blocking |
| Phase M4 | G8 evidence required → blocking；G21 / G22 启用；G23 / G24 warning |
| Phase M5 | G11 / G12 / G14 / G15 / G17 → blocking（archive ceremony 配套）|
| Phase M6 | G23 / G25 → blocking；G26 软要求；G27 blocking |

启用 / 关闭任何 blocking gate 必须 HITL（per `policies/ai-agent.md` §HITL Required Scenarios
#5）.

---

> *Phase M0 skeleton — `state: draft`. 完整 gate 矩阵 + 启用顺序 + 例外处理见 `policies/
> ci-gates.md` + Phase M2 内容填充.*
