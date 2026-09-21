---
name: mj-agent-git-review-pr
description: "适用于 mj-agent 的审别人PR架构/数据边界。输入：他人PR URL/head、diff、branch、规范。流程：定位→变更概览→F1-F3/D1-D9→草案→授权发布建议→人工决策。输出：每发现有文件/影响/依据，未测项清楚。Use when：评审另一作者PR的guardrail与模块边界。Do not use for：我的PR收到反馈请代拟回复；建议flow-review-respond，区分方向。授权：D3-D7保护审查；评论明确授权；merge人工；聊天批准不自动解锁 hook。独立调用完成后结束，委派返回调用者；不自动跨阶段、提交或发布外部消息。"
---


# mj-agent Git Review PR

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。独立调用只完成本技能；委派时记录调用者与返回阶段，同阶段必要校验完成后返回。下游 Handoff 均为建议，不能自动跨阶段或发布。受保护动作先完成可审阅草案；Owner 批准与宿主执行能力分开，hook 硬阻断时返回 `BLOCKED_EXECUTION_ROUTE`。


## 触发与职责详述

This skill should be used when the user asks to review someone else's Pull Request for architecture compliance, mj-agent module-boundary consistency, or in-source canonical / biz_catalog / SQL guardrail safety in mj-agent. Make sure to use this skill whenever the user pastes a PR URL belonging to another contributor, mentions a PR number, or asks "评审PR", "review PR", "审查PR", "PR评审", "review pull request", "这个PR能合吗", "可以merge吗", "帮我看看这个PR", "检查PR架构", "architecture review", "代码结构有没有问题", "检查一下这个分支" in the mj-agent context. Direction-distinct from mj-agent-flow-review-respond which processes review feedback received on **your own** PR (Stage 15, opposite direction). Audits **someone else's** PR with mj-agent-specific risk lenses (in-source canonical / biz_catalog / SQL guardrail / system.md version / dual-track A1-A11 self-check + engineering-workflow A12-A14). Do not use for: drafting replies to reviewer comments on your own PR (use mj-agent-flow-review-respond), pre-merge readiness check (use mj-agent-git-check-merge), or doc-only review (use mj-agent-doc-review in PR-C1).


## Overview

PR 架构评审（**审别人的** PR）— 检查 mj-agent 模块边界 / in-source canonical 改动 / biz_catalog 镜像 / SQL guardrail 红线 / dual-track A1-A11 + A12-A14 self-check。

**核心价值**：回答"这个 PR **应不应该**合"——架构合规、设计一致性、mj-agent 数据边界（ADR-006/009）安全。

与 `mj-agent-git-check-merge`（回答"**能不能**合"——冲突、CI、审批）互补。

**Direction-critical**：

| Skill | Direction | When |
|---|---|---|
| `mj-agent-git-review-pr`（本 skill） | **审别人 PR** | Architecture / 数据边界 / in-source canonical 安全 review |
| `mj-agent-flow-review-respond` | **回应自己 PR comments** | Stage 15 of HITL flow — 处理收到的 feedback |

## 前置条件

- `gh` CLI 已认证
- 在某个 mj-agent worktree 内
- 远端可访问

## 快速开始

| 输入 | 行为 |
|---|---|
| `评审 PR #65` | 完整 5 阶段评审 |
| `帮我看看 documentation/phase-b3a-flow-completion` | 通过分支名定位 PR |
| `只看 SKILL.md 改动的 PR #65` | 范围限定 |
| `PR #65 的变更概览` | 快速模式：只 Stage 1-2 |

## 工作流

### Stage 1: 定位 PR

```bash
gh pr view <input> --json number,title,state,baseRefName,headRefName,additions,deletions,changedFiles,commits
```

验证 state = OPEN；识别 mj-agent 5 branch type（feature/bugfix/documentation/maintain/hotfix；**不**用 optimization）。

**STOP & ASK**：
- **H1**: state ≠ OPEN → 终止，提示"PR #N 当前 state = X，无法评审"
- **H2**: 分支类型无法识别 → 向 Owner 询问 询问

### Stage 2: 描述变更

```bash
gh pr view <number> --json commits --jq '.commits[].messageHeadline'
gh pr diff <number> --stat 2>/dev/null || gh api repos/MJ-AgentLab/mj-agent/pulls/<number>/files --jq '.[].filename'
```

按 mj-agent 文件分类统计：

- **Code**: `src/mj_agent/**/*.py`, `tests/**/*.py`
- **In-source canonical**: `src/mj_agent/skills/**/SKILL.md`, `src/mj_agent/prompts/*.md`（**B 风味**，§3.1 必停）
- **biz_catalog**: `src/mj_agent/biz_catalog/qcm_catalog.yaml`（§3.1 必停）
- **SQL guardrail**: `src/mj_agent/tools/sql/{guardrail,precheck}.py`（§3.1 必停）
- **Config**: `*.yaml`, `*.yml`, `*.toml`, `.env*`, `langgraph.json`, `docker/*`
- **Docs**: `docs/**/*.md`, `*.md`
- **Engineering-workflow**: `.agents/skills/**`, `.codex/hooks.json`, `.codex/config.toml`
- **Other**: 不匹配以上

> **快速模式中断**：用户只要"变更概览" → 输出概览后直接 Handoff。

### Stage 3: 架构评审

#### 3.1 固定检查（必做）

| 检查 | 方法 |
|---|---|
| **F1 分支同步** | `git log HEAD..origin/<base>` 计算落后提交数 |
| **F2 变更概览** | 复用 Stage 2 |
| **F3 Commit 规范** | 提取 commit type，对照 mj-agent Branch×Type 矩阵（Commit Convention §5.2） |

#### 3.2 动态检查触发

| 变更范围 | 触发的检查 |
|---|---|
| `src/mj_agent/` 下新模块目录 | D1（mj-agent 模块边界） |
| `src/mj_agent/agent.py` / `langgraph.json` 改动 | D2（graph 装配 + Studio 入口） |
| `src/mj_agent/skills/**/SKILL.md` 改动 | **D3 in-source SKILL canonical**（§3.1 必停面 runtime-skill-content-change）+ A11 EVAL 引用审查 |
| `src/mj_agent/prompts/*.md` 改动 | **D4 system.md canonical**（§3.1 必停面 prompt-version-or-body-change）+ version bump 检查 |
| `src/mj_agent/biz_catalog/qcm_catalog.yaml` 改动 | **D5 biz catalog drift**（§3.1 必停面 biz-catalog-sync）+ scripts/diff_biz_schema.py 比对（offline 快照；缺快照时如实记未验证） |
| `src/mj_agent/tools/sql/{guardrail,precheck}.py` 改动 | **D6 SQL guardrail 放宽**（§3.1 必停面 sql-guardrail-relax）+ ADR-006/009 红线检查 |
| `docker/` / `pyproject.toml` 改动 | D7（infra；C 风味）+ uv lock 同步 |
| `docker/Dockerfile` 外部 registry 镜像引用改动（`FROM <image>` / `COPY --from=<registry image>`；内部 `COPY --from=<stage>` **不**在内） | **D7b 供应链必停**（canonical `secrets-grants-or-prod-config`；`policies/docker-runtime.md` §4）：核 Owner 拍板留痕 + PR 模板 Docker Impact 的「外部 registry 镜像引用修改」项已勾 + digest 变化经核对。**无审批类 CI gate 兜底 → 此项只能人审**（`docker-build` 只验可构建、V5 只 lint 契约）。**bot 作者 PR**（Dependabot digest bump）不渲染 PR 模板 → 拍板即 merge 决定本身，须以 PR comment 留痕 |
| `.env.example` / `secrets.enc` 改动 | D8（secret 管理）+ config/README.md 同步 |
| `docs/` 改动 | 不动态检查；输出 "建议 mj-agent-doc-review (PR-C1)" |
| `.agents/skills/` 改动 | D9（A12 description 质量）+ A12-A14 自检 |

#### 3.3 执行被触发的检查

- **D1 mj-agent 模块边界**：列新模块目录，对照 `repo:README.md` 架构概览与 `repo:src/mj_agent/AGENTS.md`
- **D2 graph 装配**：读 agent.py，确认 `_ACTIVE_SKILLS` + `make_graph` + `langgraph.json` 入口一致
- **D3 in-source SKILL**：读 SKILL.md body 改动；确认 13 字段 frontmatter（sdd/adapters/runtime-skill schema）+ 五段式 body 保持；A11 `eval_references` 同步审查
- **D4 system.md**：读 prompt body 改动；确认 frontmatter `version` bump（如适用）+ `eval_references` 同步
- **D5 biz catalog**：跑 `uv run python scripts/diff_biz_schema.py`（offline，只读
  `.mj-agent-local/biz-schema-snapshots/` 下 Owner 背书的 sanitized 快照，不连库）。**审别人的
  PR 时你本地通常没有快照**，届时会得到 `SKIP_NO_SNAPSHOT`（exit 0）——那是「未验证」，
  不是「无漂移」；如实写进 review 结论，不要因为 exit 0 就放行 D5
- **D6 SQL guardrail**：检查 BIZ_ALLOWED_DWD_TABLES 修改是否扩边界；ADR-006 4 层 guardrail / ADR-009 biz 域 only 红线
- **D7 infra**：docker compose config 校验 + pyproject.toml 改动 → uv lock 同 PR commit + .env.example 改 → secrets.enc 同步
- **D8 secret**：grep `ARK_API_KEY` / `POSTGRES_*PASSWORD` 是否硬编码
- **D9 .agents/skills/**：description ≥ 200 chars + 正向触发 + 反向触发段（A12 阻塞门禁；详见 Meta v2.1 §7.7）

**STOP & ASK**：
- **H3**: 检查项判定模糊 → 标 ⚠️ 请人工判定，继续后续

#### 3.4 汇总

```
| # | 检查项 | 结果 | 说明 |
|---|---|---|---|
| F1 | 分支同步 | ℹ️ | 同步 |
| F2 | 变更概览 | ℹ️ | Code 5 / SKILL 1 / Docs 2 |
| F3 | Commit 规范 | ✅ | 3 docs — feature/* 允许 |
| D3 | in-source SKILL canonical | **⚠️ HITL** | **B 风味 §3.1 必停面 runtime-skill-content-change**；建议先 mj-agent-runtime-skill-doc-improve propose diff |
| D9 | .agents/skills/ A12 | ✅ | description 280 chars + 正反向触发 |
```

按严重度分组：Critical > Important > Suggestion。

### Stage 4: 人工确认 → 发布 comment

向 Owner 询问 展示评审摘要 + 提供选项：

```
options:
  - "发布到 PR — 作为 comment 发到 GitHub PR"
  - "修改后发布 — 调整后再发"
  - "仅本地查看 — 不发"
```

如选发布：

```bash
gh pr comment <number> --body-file <tmp-review.md>
```

### Stage 5 — 返回人工合并决策

评审结束只交 readiness 证据与风险；即使用户要求合并，也由 Owner 人工执行。不得自动 merge/auto-merge 或顺带删除分支。后续清理另行调用并核验授权。

## 输出格式

GitHub Comment 格式（建议）：

```markdown
## PR #<id> 评审 — by Codex（mj-agent-git-review-pr）

### 变更概览
- 变更类型：<branch type> + 风味分布
- F1-F3: <表格>
- D1-D9（按触发）: <表格>

### 发现的问题
**Critical**:
- <问题 1>

**Important**:
- <问题 2>

**Suggestion**:
- <问题 3>

### 总判断: ✅ Approve / ❌ Changes Requested / ⚠️ Comments
```

结果图标：✅ 通过 | ❌ 未通过 | ⚠️ 需人工判定 | ℹ️ 信息

## Handoff

```
评审完成 ✓
  已完成：架构评审 ✓ | comment {已发布到 PR / 未发布}
  建议下一步：
  - 文档改动 → mj-agent-doc-review（PR-C1 落地）
  - 技术合并检查 → mj-agent-git-check-merge
  - 人工合并 → Owner 按 Stage 5 审阅处理
```

## What This Skill DOES NOT DO

- ❌ 不替代 `mj-agent-flow-review-respond`（方向相反——本 skill 审别人 PR；review-respond 处理自己 PR comments）
- ❌ 不替代 `mj-agent-git-check-merge`（互补——本 skill 评架构；check-merge 评技术 readiness）
- ❌ 不替代 `mj-agent-doc-review`（PR-C1 落地后 docs/ 改动专评）
- ❌ 不执行 merge，Stage 5 交 Owner 人工处理
- ❌ 不调 `mj-agent-git-sync`（仅展示 base 落后状态）

## Sub-skill / Tool Calls

| Tool / Skill | 用途 |
|---|---|
| shell `gh pr view --json` | Stage 1/2 fetch |
| shell `gh pr diff` / `gh api ...files` | Stage 2 file list |
| 读取 | Stage 3 SKILL.md / system.md / config 改动审 |
| shell `uv run python scripts/diff_biz_schema.py` | D5 biz_catalog drift（offline 快照；SKIP ≠ PASS） |
| rg | D8 secret 硬编码扫描 |
| `mj-agent-doc-review`（PR-C1） | docs/ 改动时建议运行 |
| `mj-agent-git-check-merge` | 评架构后接技术合并检查 |
| `mj-agent-git-delete` | Stage 5 合并后清理 |

## Reference Files

- `repo:sdd/workflows/execution-loop.md` §3.1（必停规则）+ `repo:policies/ai-agent.md` §4（mj-agent 专属必停 surface；D3-D6 触发依据）
- `repo:.agents/references/execution-boundaries.md`「原生配置与文档检查接口」（A12-A14）；A13 → `repo:policies/ci-gates.md` §5.1；A14 → `repo:policies/ai-agent.md` §4（D9）
- `repo:decisions/ADR-006_Fail_Safe_Reads.md` / `repo:decisions/ADR-009_Biz_Domain_As_Primary_Data_Source.md`（D6 数据边界红线）
- `repo:docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §5.2（F3 Branch×Type 矩阵）
- `repo:README.md` 架构概览与 `repo:src/mj_agent/AGENTS.md`（D1 模块边界依据）

## Anti-patterns

- **不要** 跳过 D3-D6（§3.1 必停 4 项 mj-agent 专属硬约束）
- **不要** 在 in-source canonical 改动时仅给 Approve 不要求 EVAL 引用 / Domain Expert review
- **不要** 用本 skill 处理自己 PR 的 review comments（用 `mj-agent-flow-review-respond`，方向相反）
- **不要** 把 review 结论当作合并或删分支授权
