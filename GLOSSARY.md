---
type: glossary
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# GLOSSARY

> mj-agent 全仓领域术语表（capability id / ADR 编号 / 技术栈缩写 / "上游业务系统" 等）.
> Phase M0 — 核心术语；Phase M5 docs/glossary/ 平移合并时扩充.

## A

- **A1-A14 PR gate** — mj-agent tri-track documentation governance 的 14 阻塞式 PR 检查
  （Code-Side A1-A6 + Agent-Side A7-A10 + A11 + Engineering-Workflow A12-A14）. Phase M5 末
  整合进 `policies/documentation.md` + `policies/ci-gates.md`.
- **ADR** — Architectural Decision Record；位于 `docs/adr/`（Phase M0-M5）→ `decisions/`
  （Phase M5 平移后）.
- **adapter** — `sdd/adapters/` 内 7 启用 adapter 文档；每 adapter 定义 contract schema +
  §BDD Rules + §TDD Rules + CI gate. 详 `sdd/adapters/`.
- **archive ceremony** — Phase M5 旧 STANDARD + 9 deprecated ADR + 现 docs/* 整体迁入
  `archive/` 的批量动作. 详 `policies/archive.md` + `sdd/workflows/archive-capability.md`.

## B

- **biz_dws / biz_dwd / biz_ods / biz_ads** — 上游业务系统 PostgreSQL schema 命名约定.
  mj-agent 只读访问：`biz_dws`（所有汇总表）+ `biz_dwd` 仅 2 张维度表（
  `dwd_dim_product_interface` / `dwd_dim_institution`）.
- **BDD** — Behavior-Driven Development. mj-agent Phase M1 起 capability 加 `behavior.feature`
  （Gherkin Given-When-Then）作为高风险 REQ 的行为契约；Phase M3 起 step definitions 在
  `tests/bdd/`. 详 `sdd/adapters/bdd-tdd.md`.

## C

- **capability** — mj-agent 自包含工作单元（业务能力包）；位于 `capabilities/<domain>/<slug>/`；
  含 9-artifact 套件（spec / requirements / design / contracts / tasks / runbook / trace /
  evidence）. 5 pilot capability：`data-agent.safe-sql` / `data-agent.biz-catalog` /
  `data-agent.llm-provider` / `infrastructure.docker-compose` /
  `infrastructure.mcp-server-governance`.
- **CHAINLIT_HOST/PORT** — Chainlit UI 监听地址；Phase 1 sub 1.A 启用.
- **Claude Code** — Anthropic 的 AI dev CLI；mj-agent 唯一 active dev agent. 详 `AGENTS.md` +
  `CLAUDE.md`.
- **codebase map** — `docs/INDEX.md` 在 Phase M0 升级为显式 codebase map 角色（A4）；
  Phase M5 末改写为 redirect map.
- **Codex** — OpenAI 的 AI agent；**NOT in mj-agent dev workflow**；仅作只读外部评审.
  详 `AGENTS.md` + `policies/ai-agent.md` §1.
- **contract** — `capabilities/<cap>/contracts/<slug>.contract.yml`；机器可读行为契约；
  schema 详 `sdd/adapters/`.

## D

- **DGX-Spark** — 192.168.0.189；提供本地 vLLM / SGLang / Ollama / TGI / llama.cpp OpenAI
  兼容 LLM endpoint；**不部署 mj-agent**（per ADR-027；DGX 仅算力节点）.
- **DRI** — Directly Responsible Individual；mj-agent 当前 DRI = ranzuozhou
  (zuozhouran@gmail.com).

## E

- **EVAL** — Evaluation framework；Track B 自有（per ADR-024）；位于 `tests/eval/`；
  4 子类（outcome / trajectory / component / integration）.
- **evidence** — `capabilities/<cap>/evidence/`；append-only；7 subtype（verification /
  reports / assessments / security / runtime / postmortems / **bdd** + **tdd**）.

## H

- **HITL** — Human-In-The-Loop；mj-agent 必停场景见 `policies/ai-agent.md` §4 + `sdd/gates.md`.
- **HITL Prompt v1.x** — 17-stage 执行闭环 STANDARD（位于 `docs/rule/`）；Phase M5 平移 +
  内容并入 `sdd/workflows/` 各 workflow.

## L

- **LangGraph Studio** — LangChain 的 graph debug UI；通过 `uv run langgraph dev` 启动；
  详 `docs/runbook/dev_studio_walkthrough.md`.
- **L1 / L1b / L2 / L3 / L4** — 数据-LLM 边界 4 层防御（详 `policies/data-boundary.md` §1
  原则 3 工具中介）：L1 regex（`tools/sql/guardrail.py`）/ L1b sqlglot AST
  （`tools/sql/precheck.py`）/ L2 SKILL.md semantics / L3 `default_transaction_read_only=on` /
  L4 GRANT.
- **LLM_PROVIDER** — env var；2 值：`ark`（default） / `local-openai-compat`（DGX）.
  详 ADR-027.

## M

- **mj-agent** — 本仓库；MJ-AgentLab 数据智能体；LangChain 1.x + LangGraph 1.1.8 + Python 3.13
  + uv.
- **mj-agent-* skill family** — `.claude/skills/mj-agent-<group>-<verb>/` 32 in-tree workflow
  skill；5 family（flow / git / doc / runtime / infra）+ Phase 6 新增 evidence family（4）.
- **mj_agent_memory** — mj-agent 独立 PostgreSQL DB（langgraph AsyncPostgresSaver
  checkpointer）；container = `mj-agent-postgres`；与上游业务系统 biz pg 解耦.

## P

- **policy** — `policies/` 内 9 native 文件（documentation / git-branching / ci-gates /
  ai-agent / claude-code-skill / docker-runtime / data-boundary / archive / security）.

## Q

- **qcm_catalog.yaml** — `src/mj_agent/biz_catalog/qcm_catalog.yaml`；mirror 上游业务系统数据
  字典 STANDARD；4 项专属必停之一 **biz-catalog-sync**.

## R

- **REQ-NNN** — capability `requirements.md` 内单需求条目；序号 001 单调递增.

## S

- **SDD** — Spec-Driven Development；mj-agent 治理范式 per ADR-031.
- **SKILL.md (in-source)** — `src/mj_agent/skills/<name>/SKILL.md`；13-field Agent_Side
  schema；4 项专属必停之一 **runtime-skill-content-change**.
- **SKILL.md (in-tree workflow)** — `.claude/skills/mj-agent-*/SKILL.md`；2-field ADR-013
  native schema（name + description only）.
- **spec.yml** — `capabilities/<cap>/spec.yml`；capability 元数据 schema 入口；详
  `sdd/templates/spec.yml.template`.

## T

- **TDD** — Test-Driven Development. mj-agent Phase M3 起 capability `tasks.md` 加
  `tdd.test_list[]` 字段（red-green-refactor 三阶段证据指针）；G28 contract-test-first blocking
  from Phase M3.
- **trace.yml** — `capabilities/<cap>/trace.yml`；schema v1.2 含 BDD 层（REQ → BDD → CONTRACT
  → TEST → TASK → PR → EVIDENCE）.
- **TOMBSTONE.md** — archive ceremony 时每 archived unit 顶部红 NOTE 文件（详
  `sdd/templates/tombstone.md.template`）.

## U

- **上游业务系统 / Upstream Business Warehouse** — mj-agent prose 中描述外部业务库的中性术语
  （per PR-118 D2 decision；2026-05-11 cross-repo decoupling cleanup 后）.
  - 代码层 literal（如 `mj-system-backend-network` Docker network 名 / `MJ_AGENT_PG_BIZ_*`
    env var）保留作真实部署对象的精确引用
  - prose 一律用"上游业务系统"
  - 详 `docs/glossary/upstream_business_warehouse.md`（Phase M5 末平移至本 GLOSSARY 或
    `archive/glossary/`）

---

> *Phase M0 skeleton — Phase M5 末 docs/glossary/ 平移合并时扩充更多术语.*
