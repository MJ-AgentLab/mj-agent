---
title: PLAN B — 撰写 docs/db_access.md（Phase 0 退出标准 #6 / PR2）
type: PLAN
status: 草案
owner: ranzuozhou
created: 2026-04-24
related:
  - ../README.md
  - ../src/mj_agent/tools/sql/guardrail.py
  - ../src/mj_agent/integrations/mj_system_db.py
  - ../src/mj_agent/skills/query-writing/SKILL.md
  - ../src/mj_agent/config.py
external:
  - D:/workspace/10-software-project/projects/mj-agent-design/mj-agent-roadmap-v1.6.md
  - (待确认) D:/workspace/10-software-project/projects/mj-system/.../R__analyst_permissions.sql
tags:
  - phase0
  - docs
  - pr2
  - db-access
  - adr-006
---

> **目的**：产出 `docs/db_access.md`——一份"mj-agent 怎么接触 mj-system biz 域数据"的权威说明书，作为 Phase 0 退出标准 #6 / roadmap PR2 的交付物。
> **受众**：新加入 mj-agent 的开发者、做合规/审计的同事、mj-system DBA。

## 1. 范围

| 做什么 | 不做什么 |
|---|---|
| 把 ADR-006 的四层可见性落成可操作的读者级文档 | 替代 ADR-006（ADR 讲"为什么"，本文讲"怎么做"） |
| 列出可见 schema / 表 / 凭据来源 / 运维路径 | 写查询示例大全（那在 `skills/query-writing/SKILL.md`） |
| 附 psql 验权脚本和 allowlist 扩展流程 | 承担 contract 签字（PR4 的事） |

## 2. 文档大纲（`docs/db_access.md`）

```
# mj-agent ↔ mj-system biz 域访问手册

## 0. 摘要 (TL;DR)
   一段话 + 一张 4 层图

## 1. 可见范围
   - biz_dws: 全部表（列白名单）
   - biz_dwd: 仅 2 张 dim 表（点名）
   - 不可见：biz_ods / biz_ads / 所有 ops_* schema
   - 权威来源：ADR-006

## 2. 四层可见性机制（表格 + 锚点）
   | 层 | 机制 | 代码/配置位置 | 谁维护 |
   |----|------|--------------|-------|
   | L1 | regex guardrail — single-statement, SELECT-only, schema allowlist | src/mj_agent/tools/sql/guardrail.py | mj-agent |
   | L2 | SKILL.md 声明可见表，prompt 里显式列出 | src/mj_agent/skills/query-writing/SKILL.md | mj-agent |
   | L3 | 连接级 default_transaction_read_only=on | src/mj_agent/integrations/mj_system_db.py | mj-agent |
   | L4 | DB role GRANT + statement_timeout=60s | mj-system R__analyst_permissions.sql | mj-system |

## 3. 凭据
   - 获取渠道（团队 key 分发）
   - .env 字段映射（POSTGRES_ANALYST_*, ARK_API_KEY 不在本文范围）
   - 安全守则：.env 不提交 / 不贴群 / 不入 log

## 4. 运维手册
   ### 4.1 核验 analyst 权限
      psql 命令（SELECT biz_dws / SELECT biz_ods 期望 deny / INSERT 期望 deny）
   ### 4.2 扩展 allowlist（审批 + 实施 + 验证）
      流程图 + 每一步责任人 + 回滚预案
   ### 4.3 紧急关停
      DB 侧 REVOKE 指令（模板）+ 通知链路

## 5. 相关文件
   - ADR-006（可见性四层）
   - ADR-008（连接配置基线）
   - mj-system R__analyst_permissions.sql
   - roadmap v1.6 §3 Phase 0
```

## 3. 分支

```bash
git -C develop worktree add ../documentation/db-access -b documentation/db-access develop
```

## 4. 执行步骤

### 4.1 对齐 mj-system 权威来源

1. 打开 sibling 仓库（推断路径：`D:/workspace/10-software-project/projects/mj-system/...`）
2. 定位 `R__analyst_permissions.sql`：
   - 记录：涉及的 role 名、GRANT 的 schema / 表清单、`statement_timeout` 值
3. 若该文件尚未落地 → **停笔**，先在 mj-system 侧起 issue 跟进；本 PLAN 进入阻塞态

### 4.2 起草文档

- 每个小节尽量用**代码锚点**（`file:line`）而不是泛泛的"由 mj-agent 实现"
- psql 验权命令必须可复制粘贴跑（含必要的 `-h -U -d`）
- allowlist 扩展流程用编号列表，每一步写清楚：谁发起、谁审批、怎么实施、怎么验证

### 4.3 `docs/adr/` 是否存在

核查：当前 worktree 里 `docs/adr/` 目录不存在（见 PLAN C Track C2）。
动作：本 PLAN 不负责回填 ADR，但在 `db_access.md` 里引用 ADR-006 时：

- 若 PLAN C2 已决定镜像 ADR 到本仓库 → 相对路径 `./adr/ADR-006-...md`
- 若 PLAN C2 决定只引用 mj-agent-design → 绝对外链（`../../mj-agent-design/adr/...`）

两种写法都可以，但 **先和 PLAN C2 的决策对齐**，避免落地后返工。

### 4.4 CHANGELOG

```
- phase0: add docs/db_access.md (exit criterion #6)
```

## 5. 验证清单

- [ ] 四层机制每层都有 `文件路径:行号` 级锚点
- [ ] psql 验权命令对三种场景都给了预期输出（SELECT ok / biz_ods denied / INSERT denied）
- [ ] allowlist 扩展流程覆盖：申请 → 审批 → DB 侧 GRANT → agent 侧 `BIZ_ALLOWED_SCHEMAS` → 验证
- [ ] 紧急关停章节包含 REVOKE 模板 + 通知对象清单
- [ ] ADR-006 引用路径与 PLAN C2 决策一致
- [ ] `rg -n '192\.168|analyst123|<实际IP>' docs/db_access.md` 为空（不泄密）
- [ ] `CHANGELOG.md` 已更新

## 6. 依赖与风险

| 依赖 | 风险 | 缓解 |
|---|---|---|
| `R__analyst_permissions.sql` 在 mj-system 已落地 | 文档会和真实 GRANT 脱钩 | 先核对；未落地就等 |
| PLAN C2 对 ADR 策略的决定 | 链接形式反复横跳 | 先和 C2 沟通再动笔引用段 |
| 合规（PR4）可能要求加 PII 章节 | 文档结构变动 | 在本 PR 留一个 `<!-- PR4: PII 章节 -->` 占位注释 |

## 7. PR 流程

- 走 `mj-git:mj-git-commit`（`docs(db-access): ...`）+ `mj-git:mj-git-pr`
- PR 模板：`.github/PULL_REQUEST_TEMPLATE/documentation.md`
- PR 描述链接：本 PLAN、ADR-006、roadmap Phase 0 §3 退出标准 #6

## 8. 收尾

- 合并后把本 PLAN frontmatter 的 `status` 改为 `已执行 <日期> <PR#>`
- 若本 PLAN 执行中暴露出 ADR-006 的不准确处，**不**在本 PR 改 ADR——另起 `documentation/adr-006-fix`
