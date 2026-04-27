---
type: plan
summary: PLAN C — 扩展 smoke 用例 & 回填缺失 ADR（Phase 0 退出标准 #2 / PR3）
owner: ranzuozhou
created: 2026-04-24
updated: 2026-04-27
state: draft
related:
  - ../tests/smoke/test_agent_smoke.py
  - ../tests/conftest.py
  - ../CLAUDE.md
  - ../src/mj_agent/tools/sql/guardrail.py
external:
  - D:/workspace/10-software-project/projects/mj-agent-design/mj-agent-roadmap-v1.6.md
  - D:/workspace/10-software-project/projects/mj-agent-design/adr/ (权威 ADR 来源，待核实)
tags:
  - phase0
  - tests
  - adr
  - pr3
---

> **目的**：把 Phase 0 剩下的两块"杂项"清掉——Track C1 让 smoke 覆盖达到退出标准 #2，Track C2 把 CLAUDE.md 里引用但 worktree 中并不存在的 ADR 核查一遍。
> **受众**：测试/质量负责人（C1）、架构文档维护者（C2）。

## 1. 范围（两个独立 Track，两个 PR）

| Track | 对应退出标准 | 动作 | 目标 PR |
|---|---|---|---|
| C1 | Phase 0 #2：≥ 3 真实 biz 表案例 | 在 `tests/smoke/` 加 #2–#4 | `feature/smoke-expansion` |
| C2 | CLAUDE.md 声明的 `docs/adr/` 与实际一致 | 核查 ADR 000/001/002/003/006/008/009，决定镜像/引用/stub | `documentation/adr-backfill` |

> 两个 Track 独立成 PR——review 压力不同，C1 需要跑 smoke（有外部依赖），C2 纯文档决策。

## 2. 分支策略

```bash
# C1
git -C develop worktree add ../feature/smoke-expansion -b feature/smoke-expansion develop
# C2
git -C develop worktree add ../documentation/adr-backfill -b documentation/adr-backfill develop
```

## 3. Track C1 — smoke #2–#4

### 3.1 现状

`tests/smoke/test_agent_smoke.py` 只实现了 `test_smoke_01_list_biz_tables`。文件顶部注释已显式说"Phase 0 ships smoke #1 only; cases #2–#6 land in later PRs per the plan."

Phase 0 退出标准 #2 只要求 smoke #2–#4（#5/#6 是 Phase 1）。

### 3.2 新增用例

| 用例 | 提问 | 断言 |
|---|---|---|
| `test_smoke_02_describe_biz_dws_table` | "描述 biz_dws.dws_qcm_qrynum_daily_total 的结构" | tool call 含 `describe_biz_table`；最终文本含至少一个真实列名（如 `data_date` / `day_qrynum`） |
| `test_smoke_03_execute_sql_happy_path` | "最近 7 天每天的查询总量是多少？" | tool call 含 `execute_sql`；SQL 命中 `biz_dws.dws_qcm_qrynum_daily_total`；响应里 `row_count ≤ 7` 且 `truncated == false` |
| `test_smoke_04_red_line_schema_blocked` | "查 biz_ods.ods_query_volume_daily 行数" | 工具层抛 allowlist 错（`schema 'biz_ods' is not in the allowlist`）；agent 最终消息明确拒绝 |

### 3.3 实现要点

- 复用 `_tool_calls` helper 和 `live_db` / `agent` fixture，保持与 #1 同风格
- `test_smoke_04` 断言 allowlist 错误可以有两种姿势：
  1. 检查 `tool` 消息的 content 里含错误字符串
  2. 检查最终 assistant 文本里有"不可达 / not in the allowlist / 不在白名单"字样
  两者都断言最稳
- SQL 模式校验（#3 要求命中具体表）用 `re.search` 忽略大小写 / 空白

### 3.4 CI 策略

- 维持现状：CI **不**跑 `tests/smoke`（成本高 + 依赖外部）
- smoke 只由开发者/发布负责人本地跑 `uv run pytest tests/smoke -m smoke`
- 在 README "Quick start" 里已有说明，本 PR 不动 CI workflow

### 3.5 CHANGELOG

```
- phase0: expand smoke tests to #2–#4 (exit criterion #2)
```

### 3.6 验证清单（C1）

- [ ] 本地 `uv run pytest tests/smoke -m smoke` 四条全绿（#1 + 新增三条）
- [ ] 每条测试都断言 **tool 被调用** + **最终文本符合语义**
- [ ] 没有硬编码凭据或绝对 host
- [ ] `pytest.mark.smoke` + `live_db` fixture 保持必须
- [ ] `ruff check` / `mypy` 对新测试通过

## 4. Track C2 — ADR 核查与回填

### 4.1 背景差距

`CLAUDE.md` 写：

> ADRs live in `docs/adr/`; Phase 0 ships 000/001/002/003/006/008/009.

但当前 `develop` worktree **没有** `docs/` 目录（`git ls-tree -r HEAD --name-only` 可验证）。两种可能：

1. 权威 ADR 在 sibling 仓库 `mj-agent-design/adr/`（roadmap 也在那边），本仓库是 consumer
2. Phase 0 原本就该在本仓库落地一份，只是漏了

### 4.2 决策矩阵

逐条（000/001/002/003/006/008/009）对照：

| 场景 | 选择 |
|---|---|
| `mj-agent-design` 有 + 近期不会再动 | 本仓库 `docs/adr/NNN-xxx.md` 写**一行链接 + 三句摘要**（单权威 in design 仓，本仓库只做引用锚点） |
| `mj-agent-design` 有 + 仍在迭代 | 本仓库**不**建文件；改 CLAUDE.md 的断言为 "ADRs live in `../mj-agent-design/adr/`" |
| 两处都没有 | 本仓库建 stub：frontmatter + title + `status: draft` + 3 句 motivation，占位即可，Phase 1 完善 |

### 4.3 执行步骤

1. 列出 `mj-agent-design/adr/` 下所有文件，识别 000/001/002/003/006/008/009 是否齐
2. 对每条 ADR 做上面三选一
3. 根据结果要么建 `docs/adr/` 要么改 CLAUDE.md
4. 本 PR **不写** ADR 原文（避免双权威）——如果要写原文，另起 `documentation/adr-<id>` PR

### 4.4 与 PLAN B 的协调

PLAN B 需要在 `docs/db_access.md` 里引用 ADR-006。所以：

- C2 必须**先于或同 PR** 于 B 完成（至少 ADR-006 的决策要先落）
- 若 C2 决定"本仓库镜像"，B 用相对路径
- 若 C2 决定"引用 design 仓库"，B 用绝对外链

### 4.5 CHANGELOG

```
- phase0: align ADR pointers with mj-agent-design (exit criterion pre-req)
```

### 4.6 验证清单（C2）

- [ ] 7 条 ADR 每条都有决策结果（镜像 / 引用 / stub）
- [ ] CLAUDE.md 中关于 `docs/adr/` 的断言与实际目录/链接一致
- [ ] 若存在 stub，每个 stub 文件至少含：`title` / `status: draft` / `date` frontmatter + 3 句 motivation
- [ ] 没有把同一份 ADR 同时在两仓库维护（避免 drift）
- [ ] `CHANGELOG.md` 已更新

## 5. 风险

| 风险 | 缓解 |
|---|---|
| C1：DEV 侧 `dws_qcm_qrynum_daily_total` 被改名 | 测试前跑一次 `list_biz_tables` 人工确认 |
| C1：smoke #3 依赖最近 7 天有数据 | fixture 里 skip（`pytest.skip("no recent data")`）而不是 fail |
| C2：`mj-agent-design` 路径/结构变动 | 先 `ls` 确认；如 repo 迁移先停手 |
| C2：镜像后两处 drift | 统一策略"引用为主、镜像只做链接+摘要" |

## 6. 顺序建议

- **可与 PLAN A 并行**：C2 纯文档无外部依赖；C1 需要 agent 跑通，但相对 walkthrough 本身独立
- **必须在 PLAN B 之前或同步**：B 要引用 ADR-006，路径取决于 C2 决策

## 7. PR 流程

- C1：`mj-git:mj-git-commit` → `test(smoke): add cases #2–#4` → PR 模板 `feature.md`
- C2：`docs(adr): align pointers` → PR 模板 `documentation.md`
- 两个 PR 都在描述里链回本 PLAN + roadmap §3

## 8. 收尾

- 合并后在本 PLAN frontmatter 标 `status: 已执行 <日期> PR#xx PR#yy`（两个 PR 都记上）
- 若其中一个 Track 被拆分/延后，单独改 status 并在文内注明
