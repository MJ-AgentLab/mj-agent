---
type: adr
domain: SYS
summary: 引入 archive 文件名 [DEPRECATED]_ 前缀 + frontmatter (archived/replaced-by) 规则；mj-system v5.2 §10.2 派生；partial supersede ADR-011 §5.6.2 第 2 段
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - archive
  - naming-convention
  - mj-system-derivation
  - partial-supersede
---

# ADR 019: Archive 命名规范化（[DEPRECATED]_ 前缀 + frontmatter 增强）

## Context

mj-agent Phase C-1a（PR #79）完成 active path stability（ADR-018）：active 文件名稳定，去 `_vX.Y` 后缀。但 archive 命名规则尚未引入：

- 6 个 archived 文件均**无** `[DEPRECATED]_` 前缀（视觉上与 active 文件难区分）
- frontmatter **无** `archived: <YYYY-MM-DD>` 时间戳（未来 retention policy / GC 缺乏数据基础）
- frontmatter **无** `replaced-by: <stable-path>` 字段（追溯当前活跃版本依赖手工查找 banner）

mj-system v5.2 §10.2 提供成熟的 archive 命名 + frontmatter 规则（7 步动作清单的 step 1-3）：

1. archive 文件名加 `[DEPRECATED]_` 前缀
2. legacy 文件名必带版本/时代标记（mj-agent v2.x 已遵守）
3. frontmatter 必含 `state: deprecated` + `archived: <date>` + `replaced-by: <stable-path>`

mj-system 在 v5.0 → v5.1 → v5.2 共 3 次 archive ceremony（11 份 legacy 文件）实测有效。mj-agent 私有评估（用户 2026-05-08 brainstorming，私有计划 `glistening-shannon` §C.1.2 + §C.2.1）将此识别为 P0/P1 推荐借鉴。Issue [#80](https://github.com/MJ-AgentLab/mj-agent/issues/80) 是 3-PR 序列（C → A → B）的第 3 步收尾。

## Decision

### 主条款（落 archive 文件名 + 6 archived 文件 frontmatter）

(a) **Archive 文件名必加 `[DEPRECATED]_` 前缀**：`docs/archive/rule/[DEPRECATED]_[STANDARD]_..._vX.Y.md`（与原 `_vX.Y` 后缀并存）。

(b) **frontmatter 必含**：

```yaml
state: deprecated              # 已遵守（Phase B + C-1a）
archived: <YYYY-MM-DD>         # 本 ADR 引入；归档日期戳
replaced-by: <relative-path>   # 本 ADR 引入；指向当前活跃 stable path
```

(c) **`replaced-by` 直接指向当前活跃 stable path**（无 `_vX.Y` 后缀）；不指 legacy chain 中间版本。即使框架后续 v3.0 演进，archive 文件 `replaced-by` 仍可一键追溯到现役版本。例：`Documentation_Management_Framework_v1.0` 的 `replaced-by` 直接指 `../../rule/[STANDARD]_..._Meta_Framework.md`（当前 v2.2），跳过 v1.1 / v2.0 / v2.1 中间历史版本。

### 子条款（解决 §5.9 trigger #4 解读，与 ADR-018 §4.4.4 同模式）

**Add `[DEPRECATED]_` 前缀 rename 视为 rule application**，**非** [[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]] §5.9 trigger #4 "改名"。

理由与 ADR-018 §4.4.4 一致：rename 是 rule application（首次应用本 ADR 主条款），non substantive content evolution。若视为 archive ceremony 触发，则需把已 archived 的文件再 archive，形成套娃 — 不合理。

### Archive body 内部 wikilinks 不强制更新

per mj-system §10.3 line 666："归档版本中的相对链接 不强制更新（视为冻结快照）"。本 ADR 沿用此原则：

- 6 archived 文件 body 内部对其他 archived 文件 / active 文件的 wikilinks 视为 frozen snapshot
- 接受 archived body 内 wikilinks 可能 "断链"（如指向 v1.1 文件名而该文件已 rename）
- archive INDEX（docs/archive/rule/INDEX.md，待 Phase C-3 引入）将提供 forward gateway

### Partial supersede [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]

| ADR-011 §条款 | 处置 | 说明 |
|---|---|---|
| §5.6.2 第 2 段（file move step naming + frontmatter） | **修正 supersede** | 改为：archive 必加 `[DEPRECATED]_` 前缀；frontmatter 必含 `archived` + `replaced-by` |
| §5.6.1 HITL trigger | **保留**（已被 ADR-017 §5.9 量化） | unchanged |
| §5.6.3 archive 目录语义 | **保留** | unchanged |
| §5.6.4 Living/Frozen 引用判定 | **保留** | unchanged |
| §4.2 filename rule | **已被 ADR-018 反转 supersede** | 不属本 ADR scope |
| §5.6.2 第 1 段（active filename pattern） | **已被 ADR-018 反转 supersede** | 不属本 ADR scope |

ADR-011 整体 `state: active` 不变；本 ADR-019 是第三个 partial supersede（前两个：ADR-017 §5.6.1 量化；ADR-018 §4.2 + §5.6.2 第 1 段反转）。

## Consequences

### 正面

1. **archive 文件名一眼可识 deprecated** — 文件浏览 / IDE 自动补全 / git blame 立即区分 active vs archive
2. **`archived: <date>` 提供 retention policy / GC 数据基础** — Phase C-3+ 可基于此实现 "archive 6 个月后自动 GC" 等策略
3. **`replaced-by` 一键追溯** — 直接指向 stable path，跳过 legacy chain；archive 升级后仍精确（mj-system §10.2 line 653 模式）
4. **mj-system v5.2 双向兼容** — 同源派生；未来 cross-project 协作降摩擦
5. **3-PR 序列收尾** — Phase C-2（ADR-017）+ Phase C-1a（ADR-018）+ Phase C-1b（ADR-019）三个 ADR 共同完成 mj-system v5.2 §4.1 + §10.1 + §10.2 派生

### 负面

1. **与 ADR-017 / ADR-018 形成 "三重 partial supersede ADR-011"** — reviewer 需读 ADR-011 + 三个 partial supersede ADR 才完整；§References 详记
2. **`scripts/check_wikilinks.py` NEEDLES 仍硬编码** — Phase C-3 通用化（auto-discover from `docs/archive/`）推迟
3. **archived body 内部 wikilinks 不更新** — 接受 mj-system §10.3 frozen snapshot 原则；可能 archive 内 wikilinks 404；archive INDEX 待 Phase C-3 提供 forward gateway

### 中性

1. **ADR-011 整体 `state: active` 不变** — 仅条款细化；与 ADR-017/018 模式一致
2. **自洽 dogfood**：本 PR 6 archive rename 不触发 archive ceremony（rule application 解读；§Decision 子条款）；这是 ADR-017 §5.9 触发表的第三个 dogfood 案例（C-2 反例 / C-1a 正例 / C-1b rule application）
3. **archived 字段值统一为 2026-05-09** — 实际历史归档日期（v1.0/v1.1: ~2026-04-25；v2.0 trio: ~2026-04-29；v2.1: 2026-05-09）参差；本 PR 简化为统一 frontmatter 落地日期；如需历史精确性，可 Phase C-3 时回填

## Alternatives considered

### A. 不加 `[DEPRECATED]_` 前缀（仅加 frontmatter）

内容：保留原 archive 文件名 `[STANDARD]_..._vX.Y.md`；只通过 frontmatter `state: deprecated` + `archived` + `replaced-by` 字段标记。

**拒绝原因**：(a) 文件浏览时视觉辨识度低；(b) mj-system v5.2 实测前缀有显著辨识价值；(c) 与 mj-system 双向兼容更难（mj-system 用 `[DEPRECATED]_` 前缀的 grep / scripts 在 mj-agent 失效）。

### B. archived body 内部 wikilinks 同步更新

内容：除 frontmatter 外，把 archived 文件 body 内对其他 archived / active 文件的 wikilinks 全部更新为新路径（含 `[DEPRECATED]_` 前缀或 stable path）。

**拒绝原因**：(a) 违反 mj-system §10.3 line 666 frozen snapshot 原则；(b) 历史 archive 应保留"事故时引用状态"，更新使其失去 cite-by-vintage 价值；(c) Phase C-1a 实测部分 archive 内部 wikilinks 已被 bulk replace 误改（lookbehind 不完美），导致 archive 部分内容偏离历史；本 PR 不进一步加重该偏离。

### C. 等 Phase D 与 EVAL framework 一起落地

内容：把 archive 命名规范化推迟到 Phase D（与 EVAL framework / 模板补全等同期落地）。

**拒绝原因**：(a) 用户 2026-05-09 选定 3-PR 序列（C → A → B），C-1b 是收尾步；(b) 推迟会让 Phase C-1a 引入的 v2.1 archive 长期处于 "无 [DEPRECATED]_ 前缀 + 无 archived/replaced-by 字段" 不一致状态；(c) Phase C-1b scope 自洽（仅 archive 改动），与 EVAL framework 解耦更安全。

### D. 历史归档日期回填（精确 archived 字段）

内容：v1.0/v1.1 用 `archived: 2026-04-25`（ADR-011 落地日）；v2.0 trio 用 `archived: 2026-04-29`（Phase B PR-B3c-promote 完成日）；v2.1 用 `archived: 2026-05-09`（Phase C-1a）。

**拒绝原因**：(a) 历史精确性 vs PR 简洁性的 tradeoff；(b) 实际归档日期需查 git log + ADR 落地日，工作量大；(c) Phase C-3 可在 retention policy / GC 实现时回填；(d) 当前统一 2026-05-09 表达 "archived 字段引入日期"，语义清晰。

## References

- 派生源：[mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md §10.2](https://github.com/MJ-AgentLab/mj-system/blob/develop/docs/rule/%5BSTANDARD%5D_Documentation_Management_Framework.md) lines 642-660（7 步动作清单 step 1-3）
- 关联 ADR（三重 partial supersede ADR-011 + 互不重叠）：
  - [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]：partial supersede §5.6.2 第 2 段；§5.6.1 / §5.6.3 / §5.6.4 sustained
  - [[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]]：§5.9 trigger #4 与本 rename 互不触发（rule application 解读，§Decision 子条款）
  - [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]：active path stability；§4.4.4 rule application 模式与本 ADR 同；§References 互引
- 落地：6 archived 文件 frontmatter 增强 + git mv 加 `[DEPRECATED]_` 前缀
- 关联 GitHub Issue：[#80](https://github.com/MJ-AgentLab/mj-agent/issues/80)
- 私有评估：用户 2026-05-08 brainstorming + 2026-05-09 三步序列选定（C → A → B）+ HITL Gate 1 批准（Phase C-1b Stage 5）
- 后续（不在本 PR）：Phase C-3+ scripts/check_wikilinks.py 通用化（auto-discover from `docs/archive/`，不再硬编码 NEEDLES）
