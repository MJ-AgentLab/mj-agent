---
type: guide
domain: SYS
summary: mj-agent SPEC 撰写指南 — 8 类任务识别 + TEMPLATE_SPEC.md 章节裁剪规则；HITL Stage 6 SPEC 作者必读
tags:
  - guide
  - spec
  - authoring
  - hitl-stage-6
aliases:
  - mj-agent SPEC Authoring Guide
  - mj-agent SPEC 撰写指南
created: 2026-05-11
updated: 2026-08-04
state: draft
version: v0.2
track: shared
owner: 项目负责人
---

# mj-agent SPEC 撰写指南

> **适用范围**：mj-agent 仓内所有 `docs/design/<module>/[SPEC]_*.md` 起草与更新（HITL Stage 6）
> **目标受众**：SPEC 起草者（开发 / AI Agent / Reviewer）
> **版本**：v0.2
> **关联文档**：[[../_templates/TEMPLATE_SPEC|TEMPLATE_SPEC]]、[[sdd/workflows/execution-loop|执行闭环 workflow]]（Stage 6 SPEC 起草）

---

## §1 Purpose

mj-agent 物理上只有 **1 份 SPEC 模板**（[[../_templates/TEMPLATE_SPEC|TEMPLATE_SPEC.md]]，9 段骨架：Context / Scope / Contract / Configuration / Error handling / Rollback / Verification / Observability / Open questions）。

但治理上 mj-agent 的 SPEC 任务跨 **8 类不同性质**，每类需要的章节深度不同：例如 in-source canonical（runtime LLM 上下文）SPEC 不需要 §3.1 输入 schema，但**必须**有 §7.3 EVAL 覆盖；docker compose SPEC 几乎不需要 §3 Contract，但**必须**有 §4 Configuration + §6 Rollback。

本 GUIDE 提供：

1. **§3 任务类型识别决策树**：按改动文件路径 5 秒判定任务类型
2. **§4 8 类任务详解**：每类的必填段 / 可选段 / 常见 anti-pattern
3. **§5 与执行闭环的引用映射**：执行闭环各 stage（SPEC 起草 / Self-review 等）中提到 SPEC-* 短码时如何对应到 TEMPLATE_SPEC.md 的具体 subsection
4. **§6 与 §3.1 必停规则的关系**：哪些任务类型自动触发 mj-agent 专属必停 4 项

---

## §2 通用骨架（[[../_templates/TEMPLATE_SPEC|TEMPLATE_SPEC.md]] 9 段）

| § | 段名 | 通用性 |
|---|---|---|
| §1 | Context（背景） | 8/8 类必填（任何 SPEC 都需说"为什么写"） |
| §2 | Scope（In-scope / Out-of-scope） | 8/8 类必填 |
| §3 | Contract（输入 / 输出 / 不变量 / 幂等性） | 6/8 类必填；任务类型 4/5 部分可选 |
| §4 | Configuration | 5/8 类必填；任务类型 1/3 部分可选 |
| §5 | Error handling | 6/8 类必填；任务类型 7/8 多数 N/A |
| §6 | Rollback / Compatibility | 4/8 类必填；任务类型 1/3 多数 N/A |
| §7 | Verification | 8/8 类必填（无可不写） |
| §8 | Observability | 5/8 类必填；任务类型 5/6/8 多数 N/A |
| §9 | Open questions | 任意；起草发现而不影响 v0.1 promote 的项 |

> **写法约定**：某段"不涉及"时**显式**写 `§X 不涉及（理由：...）`，**不要**保留空标题或 TODO 占位（per [[policies/documentation|documentation policy]] §5.2 OB3 内容边界）。

---

## §3 任务类型识别决策树

按 git diff 中**主要**改动文件路径 5 秒判定（多类共触时取主导类，次要类在 SPEC §1 Context 中说明）：

```text
git diff --name-only HEAD
├─ src/mj_agent/{agent,llm,tools/biz_context,memory,integrations,server,ui}/*.py
│  └─ #1 Python 应用代码
├─ src/mj_agent/tools/sql/{guardrail,precheck,execute,introspect}.py
│  └─ #2 SQL guardrail / 数据边界
├─ src/mj_agent/skills/**/SKILL.md  OR  src/mj_agent/prompts/*.md  OR  src/mj_agent/biz_catalog/qcm_catalog.yaml
│  └─ #3 In-source canonical（runtime LLM 上下文）— mj-agent 专属，永远 HITL
├─ docker/**  OR  docker/compose*.yml
│  └─ #4 Docker compose + storage stack
├─ .github/workflows/**  OR  scripts/*.{py,ps1}
│  └─ #5 CI/CD + scripts 自动化
├─ .env.example  OR  config/secrets*.{enc,conf,yml}  OR  pyproject.toml  OR  uv.lock
│  └─ #6 Config / secrets / dependencies
├─ .claude/skills/mj-agent-*/SKILL.md  OR  .mcp.json
│  └─ #7 Engineering-workflow infra（mj-agent 专属）
└─ docs/**/*.md  OR  CLAUDE.md  OR  INDEX.md
   └─ #8 文档治理
```

**多类共触示例**：

- 改 `src/mj_agent/llm.py` + `.env.example` 新增 `LLM_PROVIDER` → 主导 #1，次要 #6（在 SPEC §1 Context 注明）
- 改 `qcm_catalog.yaml` + `src/mj_agent/biz_catalog/finder.py` → 主导 #3（in-source canonical 优先级最高），次要 #1
- 改 `docker/compose.yaml` + `.env.example` → 主导 #4，次要 #6

---

## §4 8 类任务详解

### §4.1 Python 应用代码

- **适用范围**：`src/mj_agent/{agent,llm,tools/biz_context,memory,integrations,server,ui}/`；新增 tool / 调整 agent wiring / 修改 integration
- **必填段**：§1 Context + §2 Scope + §3 Contract（全 4 子段：输入 schema / 输出 schema / 行为不变量 / 幂等性）+ §5 Error handling + §7 Verification（unit + integration）+ §8 Observability（log + LangSmith trace）
- **可选 / 多数 N/A 段**：§4 Configuration（多数无外部可调；如有则填）；§6 Rollback（API 重命名 / 删除时填）
- **常见 anti-pattern**：
  - ❌ §3.1 输入 schema 跳过 pydantic field 等价定义（mj-agent 习惯用 pydantic）
  - ❌ §3.3 行为不变量只写 happy path，不写边界条件
  - ❌ §7 仅写 "见 tests/"，不列出对应每个不变量的具体 test
- **范例**：（Phase 1 内首批 SPEC 起草后回填）

### §4.2 SQL guardrail / 数据边界

- **适用范围**：`src/mj_agent/tools/sql/{guardrail,precheck,execute,introspect}.py`；ADR-006 4 层 guardrail 调整（**注意：mj-agent 是 read-only 消费者，无 DDL/migration 范畴**）
- **必填段**：§1 Context（必引 ADR-006 / ADR-009 红线）+ §2 Scope + §3 Contract 全 + §5 Error handling（含 statement_timeout 60s 友好提示）+ §6 Rollback（guardrail 放宽 → 紧缩的兼容路径）+ §7 Verification（必含 R1/R2 red-line 探针）+ §8 Observability
- **可选 / 多数 N/A 段**：§4 Configuration（除非新增可调阈值）
- **常见 anti-pattern**：
  - ❌ Scope 中漏写 "不涉及 DDL / migration"（mj-agent 永远只读，必须显式声明）
  - ❌ §6 Rollback 写 "不涉及"（guardrail 放宽是 §3.1 必停面 sql-guardrail-relax；必须有回滚路径）
  - ❌ §7 漏 R1（biz_ods 拒绝）/ R2（导出全部）红线探针

### §4.3 In-source canonical（runtime LLM 上下文）— mj-agent 专属

- **适用范围**：`src/mj_agent/skills/**/SKILL.md`、`src/mj_agent/prompts/*.md`、`src/mj_agent/biz_catalog/qcm_catalog.yaml`
- **永远触发** [[policies/ai-agent|ai-agent policy]] §4 必停 trigger 10 / 11 / 12（视改动文件而定）
- **必填段**：§1 Context（必说明为何 LLM 行为变化）+ §2 Scope + §3.3 行为不变量（LLM 输出契约，非 schema）+ §5 Error handling（degradation 行为）+ §7 Verification（必含 §7.3 EVAL coverage；A8/A11 transitional waiver 期内可注释 TODO）+ §8.3 LangSmith trace metadata + **新增 "frontmatter strip 契约" 子段**（说明 loader 行为不变；不允许把 frontmatter 字段塞进 body）
- **可选 / 多数 N/A 段**：§3.1 输入 schema / §3.2 输出 schema（不适用 LLM body）；§4 Configuration（除非引入新 hyperparameter）；§6 Rollback（version 回退路径必填）
- **常见 anti-pattern**：
  - ❌ §7.3 EVAL coverage 直接写 "TBD"（即使 transitional waiver 也要写 backlog ticket 链接）
  - ❌ frontmatter strip 契约段缺失 → loader 行为可能漂移
  - ❌ 五段式 body 结构（Purpose / When to use / Planning workflow / Common patterns / Anti-patterns）破坏 → 见 [[sdd/adapters/runtime-skill|runtime-skill adapter]]

### §4.4 Docker compose + storage stack

- **适用范围**：`docker/`、`docker/compose*.yml`、`docker/postgres-init/*.sh`、storage stack（mj-agent-postgres + mj-agent-redis）
- **必填段**：§1 Context + §2 Scope + §4 Configuration（环境变量 / volume / network 全列）+ §5 Error handling（healthcheck 失败处置）+ §6 Rollback（compose down 步骤 + 数据保留 / 清空选项）+ §7 Verification（compose up/down 排练 + healthcheck + 跨 profile dev/test/prod 验证）+ §8 Observability（容器日志 / 健康端点）
- **可选 / 多数 N/A 段**：§3 Contract（infra 类不涉及 schema）
- **常见 anti-pattern**：
  - ❌ §4 漏 4-file profile 分层说明（per ADR-025；base + override + test + prod）
  - ❌ §6 Rollback 漏 `down -v` vs `down -v --rmi local` 三级安全说明
  - ❌ Verification 跳过 `mj-agent-infra-env-teardown` skill 的 H1/H2/H3 hard-confirm 路径

### §4.5 CI/CD + scripts 自动化

- **适用范围**：`.github/workflows/`、`scripts/*.{py,ps1}`（含 `setup-env.ps1` / `check_*.py` / `find_*.py` / `diff_*.py` 等）
- **必填段**：§1 Context + §2 Scope + §4 Configuration（trigger / matrix / secret 引用）+ §5 Error handling（脚本失败行为 / CI fail-fast vs continue-on-error）+ §7 Verification（本地运行命令 + CI dry-run 路径）
- **可选 / 多数 N/A 段**：§3 Contract（脚本类一般无契约；如有 stdout schema 则填）；§6 Rollback（脚本可幂等重跑则 N/A）；§8 Observability（CI 自带日志）
- **常见 anti-pattern**：
  - ❌ §1 Context 跳过 "为什么本脚本不能放到 mj-agent CLI"（避免 scripts/ 与 src/mj_agent/server/cli.py 职责混淆）
  - ❌ §4 漏标 secret 依赖（如 `MJ_AGENT_SSH_*` 是否需要 setup-mcp-env.ps1）
  - ❌ Verification 仅写 "CI 跑过"，不给出本地 reproduce 命令

### §4.6 Config / secrets / dependencies

- **适用范围**：`.env.example`、`config/secrets.enc` / `config/secrets.example` / `config/secrets.conf`、`pyproject.toml`、`uv.lock`
- **必填段**：§1 Context + §2 Scope + §4 Configuration（新增 / 修改 var 全列；含 default / range / 何时调）+ §5 Error handling（缺 var 时 healthcheck 行为）+ §6 Rollback（密钥轮换 / dep 降级路径）+ §7 Verification（`mj-agent check` healthcheck + setup-env.ps1 drift 检测）
- **可选 / 多数 N/A 段**：§3 Contract（schema 类一般 N/A）；§8 Observability（secret 不能 log；除非是非敏感 var）
- **常见 anti-pattern**：
  - ❌ §4 新增 var 漏同步 `setup-env.ps1` 的 `[DRIFT]` 检测清单（导致 dev 已有 .env 永远漏 var）
  - ❌ §6 Rollback 漏 `setup-mcp-env.ps1 -Reload` 流程（HKCU env var 不会自动刷新到运行中进程）
  - ❌ §7 Verification 跳过 cross-profile（dev / test / prod）的 var 集合差异说明

### §4.7 Engineering-workflow infra（mj-agent 专属）

- **适用范围**：`.claude/skills/mj-agent-*/SKILL.md`（5 family：flow / git / doc / runtime / infra）+ `.mcp.json` server 配置 + `.claude/settings.json`
- **必填段**：§1 Context + §2 Scope + §3 Contract（SKILL frontmatter schema：name + description；ADR-013 native 2-field schema；description ≥ 200 chars + 反向触发段）+ §7 Verification（A12-A14 PR 门禁通过 + skill triggering 5-iteration eval 推荐但非阻塞）
- **可选 / 多数 N/A 段**：§4 Configuration（除非引入新 settings.json 字段）；§5 Error handling（skill 失败由用户重试，无系统级 error handling）；§6 Rollback（git revert 即可）；§8 Observability（无 telemetry）
- **常见 anti-pattern**：
  - ❌ §3 Contract 漏 description "Do not use for:" 反向触发段（A12 阻塞门禁）
  - ❌ runtime 类目 SKILL 缺 "Anti-patterns" 段的 "Do NOT modify src/mj_agent/..." 硬约束
  - ❌ §7 Verification 漏 `.mcp.json` 改动后的 `/doctor` Missing-env 验证

### §4.8 文档治理

- **适用范围**：`docs/**/*.md` canonical（STANDARD / SPEC / ADR / GUIDE / RUNBOOK / POSTMORTEM / ASSESSMENT / EVAL / CONTRACT / ISSUE）+ `docs/INDEX.md` + `docs/**/INDEX.md` + `CLAUDE.md`
- **必填段**：§1 Context + §2 Scope + §7 Verification（必跑 `scripts/check_frontmatter.py` + `scripts/check_wikilinks.py`；如改 STANDARD/SPEC/ADR 触 A1-A6 全检；如改 in-source canonical 触 A7-A10）
- **可选 / 多数 N/A 段**：§3 Contract（文档不是 runtime 实体）；§4 Configuration（除非新增 frontmatter 字段）；§5 Error handling（N/A）；§6 Rollback（git revert）；§8 Observability（N/A）
- **常见 anti-pattern**：
  - ❌ §7 跳过人读端到端验证（自动化校验过 ≠ 阅读体验过；尤其 STANDARD / GUIDE 类）
  - ❌ INDEX.md 改动漏 cross-ref 一致性（新增 entry 但未更新 ADR/RUNBOOK 入口）
  - ❌ allowlist 文档（per [[policies/documentation|documentation policy]] §7.1）改动跳过 CLAUDE.md 同步检查（A6 阻塞）

---

## §5 与执行闭环的引用映射

[[sdd/workflows/execution-loop|执行闭环 workflow]] 多处用 `Contract.Input` / `Configuration` / `Error handling` 等短码标记 SPEC 漏项（替代旧 `SPEC-*` 短码 prefix）；下表给出本 GUIDE / TEMPLATE_SPEC 章节 ↔ 短码映射：

| 执行闭环短码 | TEMPLATE_SPEC.md 章节 | 本 GUIDE 章节 |
|---|---|---|
| `Contract.Input` | §3.1 输入 schema | §4 各类任务的"必填段" |
| `Contract.Output` | §3.2 输出 schema | 同上 |
| `Contract.Invariants` | §3.3 行为不变量 | 同上 |
| `Contract.Idempotency` | §3.4 幂等性 / 重试语义 | 同上 |
| `Configuration` | §4 Configuration | §4.4 / §4.5 / §4.6 必填 |
| `Error handling` | §5 Error handling | §4.1 / §4.2 / §4.3 / §4.4 / §4.5 / §4.6 必填 |
| `Rollback` | §6 Rollback / Compatibility | §4.2 / §4.4 / §4.6 必填 |
| `Verification` | §7 Verification | 8/8 类必填 |
| `Observability` | §8 Observability | §4.1 / §4.2 / §4.4 必填 |

**典型用法**：执行闭环 §6 AI Self-review（SPEC Delta Check）输出示例：

```
SPEC Delta:
- Contract.Idempotency: §3.4 未说明 retry 是否产生副作用（任务类型 #1 必填）
- Verification: §7.2 漏 integration test 路径（任务类型 #1 必填）
```

---

## §6 与 §3.1 必停规则的关系

[[policies/ai-agent|ai-agent policy]] §4 现为 **canonical 10-enum**（4 项 in-source 必停打头 + 6 项工程面；无「通用/专属」双轨编号——执行期通用暂停清单另见 [[sdd/workflows/execution-loop|execution-loop]] §3.1，两套分类并存不混编号）。下表标注哪些任务类型自动触发哪些 canonical enum：

| 任务类型 | 自动触发的 ai-agent §4 canonical enum |
|---|---|
| #1 Python 应用代码 | 多数无 §4 enum（执行期暂停走 execution-loop §3.1）；触 `capabilities/*/contracts/*` → declared-contract-change |
| #2 SQL guardrail | **sql-guardrail-relax**（永远必停） |
| #3 In-source canonical | **runtime-skill-content-change / prompt-version-or-body-change / biz-catalog-sync**（永远必停） |
| #4 Docker compose + storage stack | secrets-grants-or-prod-config（`docker/compose.prod.yml`；**及 `docker/Dockerfile` 外部 registry 镜像引用**，per #413）/ database-migration（mj_agent_memory schema） |
| #5 CI/CD + scripts | ci-blocking-gate-toggle（gate blocking flip 时） |
| #6 Config / secrets / deps | secrets-grants-or-prod-config（secret / GRANT / prod 配置）；新依赖属 execution-loop §3.1 执行期暂停，非 §4 enum |
| #7 Engineering-workflow infra | mcp-server-trust-posture-change（`.mcp.json` 面）；A12-A14 PR 门禁阻塞 |
| #8 文档治理 | bulk-content-purge-or-migration（≥10 文件迁移/归档）；其余一般无 §4 enum（framework STANDARD 触 A6 CLAUDE.md 同步） |

**SPEC §1 Context 必须显式标注本 SPEC 触发的 ai-agent §4 必停项**，让 reviewer 一眼判定 HITL 强度。

---

## §7 何时不需要写 SPEC

并非所有改动都需要 SPEC。下列场景按 [[sdd/workflows/execution-loop|执行闭环 workflow]] §3 自主处理，**不**需要走 Stage 6 SPEC：

- 拼写 / 链接 / frontmatter 小修
- lint 修复
- 局部测试补充（不变接口）
- 与代码变更直接对应的文档同步（一对一映射）
- 已有 SPEC 的 typo / 术语统一

如不确定是否要写 SPEC，先走 [[sdd/workflows/execution-loop|执行闭环 workflow]] Repo Scan 阶段，其 Documentation Decision 矩阵会判定 SPEC = Create / Update / None。

---

## §8 Open Questions

- 任务类型 #3（in-source canonical）的 EVAL coverage 子段格式 — 等 Phase 2 EVAL framework 落地后回填具体范例
- 任务类型 #7 SKILL 5-iteration trigger eval 是否升 PR 阻塞 — Phase D+ 评估
- 多类共触场景下 SPEC 的 task_type frontmatter 是否支持 multi-value — Phase 2+ 视实践决定

---

## 关联文档

- [[../_templates/TEMPLATE_SPEC|TEMPLATE_SPEC.md]]（本 GUIDE 指导填写的目标模板）
- [[sdd/workflows/execution-loop|执行闭环 workflow]]（Stage 6 SPEC 起草；引用本 GUIDE）
- [[policies/documentation|documentation policy]]（SPEC 是 code-track 文档；§5 PR 门禁）
- [[sdd/adapters/runtime-skill|runtime-skill adapter]]（任务类型 #3 in-source canonical 治理）
- [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]（任务类型 #2 SQL guardrail 红线）
- [[decisions/ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]（任务类型 #2 数据边界）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-11 | v0.1 | 初稿（PR-118 commit-3 落地；G3 gap 修复；mj-agent 8 类任务分类，区别于 mj-system 8 类） |
