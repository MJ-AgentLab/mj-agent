---
type: adr
domain: SYS
summary: 引入 active canonical 路径稳定原则（active 文件名默认无 _vX.Y 后缀；mj-system v5.2 §4.1 派生）；partial supersede ADR-011 §4.2 + §5.6.2；落 Meta v2.2 §4.4
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - filename-convention
  - active-path-stability
  - mj-system-derivation
  - partial-supersede
---

# ADR 018: Active Canonical 路径稳定原则

## Context

[[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §Decision Q1 motivation "Filename-as-version-signal" 在 Phase A→B 实测中显著低估了 audit 成本：

| 阶段 | 估计 | 实测 |
|---|---|---|
| ADR-011 设计期（2026-04-25） | ~24 reference / 14 文件 / 1 次 minor bump | — |
| Phase A→B 实际（v2.0 → v2.1 promote） | — | ~50+ reference / 多文件 / 1 次 minor bump |
| Phase C-1a Repo Scan（pre-execution） | — | **511 reference / 82 文件 / 多个 minor bump 累积** |

ADR-011 §Consequences "负面"第一条已明确承认此痛点：

> 每次正式版本演进需要 corpus-wide reference audit——本 PR 落地时审计 14 个文件 / 24 处引用

实测 21× 于设计期估计。每次 minor bump（如 v2.0 → v2.1 → v2.2）触发的 corpus rename + reference audit 已成为不可持续的治理负担。

mj-system v5.2 §4.1 + changelog 2026-05-05 引入 active path stability 规则：active canonical 文件名**默认无 `_vX.Y` 后缀**；版本仅在 frontmatter `version`。mj-system 在 1 个月使用中实测有效（避免每次 bump 的 rename 风暴）。

mj-agent 私有评估（用户 2026-05-08 brainstorming，私有计划 `glistening-shannon` §C.1.1 / §D.3）将此识别为 P0 强烈推荐借鉴项。Issue [#78](https://github.com/MJ-AgentLab/issues/78) 是 3-PR 序列（C → A → B）的第 2 步。

## Decision

### 主条款（落 Meta v2.2 §4.4 主条款）

(a) **Active canonical 文件名默认无 `_vX.Y` 后缀**；文件名保持稳定路径。例如本框架元层的稳定路径是 `[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`，而不是带版本后缀。

(b) **文档语义版本写在 frontmatter `version` 字段和正文版本说明里**，不写进文件名。

(c) **Legacy 反向规则**：归档文件**必须**保留 `_vX.Y` 或 `_pre_vX.Y` 后缀（cite-by-vintage 保留；ADR-011 §5.6 motivation Q1 在 archive 范围仍有效）。

### 例外条款

仅"多 active 主版本确需并存"（如 v1/v2 API 长期共存的 STANDARD）才允许文件名加 `_vX.Y` 区分；这是例外而非默认。

### 子条款（解决 §5.9 trigger #4 解读）

**drop `_vX.Y` 后缀的 rename 视为 rule application**，**非** [[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]] §5.9 trigger #4 "改名"。

仅当 STANDARD **同时**发生 substantive content evolution（§5.9 trigger #1/#2/#3 之一）时才触发 archive ceremony。

**先例**：mj-system v5.2 引入 stable-path 规则时同样：框架文件 archive（substantive 演进 + 改名双重）；其他 STANDARDs rename only（rule application）。本 PR Phase C-1a 沿此模式：Meta v2.1 archive ceremony；其他 5 STANDARDs（Code_Side / Agent_Side / HITL_Prompt / Commit_Message / GitHub_Markdown）in-place rename only。

### Partial supersede [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]

| ADR-011 §条款 | 处置 | 说明 |
|---|---|---|
| §4.2 filename rule（"`version` 必填类型 filename 必带 `_vX.Y`"） | **反转 supersede** | 改为：active 默认无后缀；多 active 主版本并存例外允许 |
| §5.6.2 file-move-step（"老文件 archive；新文件 `_v<new>.md`"） | **修正 supersede** | 改为：老文件 archive 保留版本后缀；新 active 无后缀 |
| §5.6.1 HITL trigger | **保留**（已被 ADR-017 §5.9 量化） | unchanged |
| §5.6.3 archive 目录语义 | **保留** | unchanged |
| §5.6.4 Living/Frozen 引用判定 | **保留** | 仍适用（lookbehind 保护 archive 路径） |
| §3.6 archive subdir 用途 | **保留** | unchanged |
| §5.5 in-source canonical 例外 | **保留** | unchanged |

ADR-011 整体 `state: active` 不变；本 ADR-018 仅细化 / 反转 §4.2 + §5.6.2 两项条款。

## Consequences

### 正面

1. **消除每次 minor bump 的 corpus-wide rename 风暴** — 实测 ~500 ref / 82 files；本 PR 是最后一次（之后 v2.2 → v2.3 等 minor bump 仅改 frontmatter `version`，无 rename）
2. **与 mj-system 文档治理双向兼容** — 同源派生，未来 cross-project 协作降摩擦
3. **PR_TEMPLATE.md 等"过时引用"自动随 active stable path 修复** — 一次性顺手解决 Phase B 漏改
4. **filename 不再表达版本信息** — 但 frontmatter `version` 字段保留语义版本；cite-by-vintage 通过 archive 保留
5. **审计工具化** — `scripts/check_wikilinks.py` NEEDLES list 确保 LIVING refs 不会无意指向 archived

### 负面

1. **反转 ADR-011 已 accepted 决策**（需正面论证；本 §Context + §Alternatives 详细记录）
2. **"rule application vs §5.9 trigger #4"解读边界**仍含主观判断（mj-system 1 月实践无歧义；mj-agent Phase 1 末复盘窗口可调整）
3. **`scripts/check_wikilinks.py` NEEDLES list** 临时方案；Phase C-3 通用化重写
4. **本 PR 一次性 ~500 ref audit** — 最后一次 corpus rename 风暴；之后稳定

### 中性

1. **ADR-011 状态不变**（仍 active；仅 partial supersede §4.2 + §5.6.2）
2. **自洽 dogfood**：本 PR 触发 ADR-017 §5.9 trigger #4（仅 Meta v2.1 → v2.2 archive ceremony 部分）；其他 5 STANDARDs 解读为 rule application（§4.4.4 + 本 ADR §Decision 子条款）
3. **5 STANDARDs git history 通过 git mv 保留** — IDE / GitHub blame / 链接稳定性不受影响
4. **filename 不再含版本** — IDE 自动补全可能稍微减少识别度；mitigated by frontmatter `version` 字段

## Alternatives considered

### A. 保持 ADR-011 §4.2 filename rule（不去版本化）

内容：文件名继续带 `_vX.Y`；每次 bump 接受 ~500 ref audit 作为治理成本。

**拒绝原因**：实测 audit 成本远超 ADR-011 §Consequences 设计期估计（21× 偏差）；每次 minor bump 的 rename 风暴不可持续。Phase A→B 实测中已形成事实漂移（PR_TEMPLATE 漏改 / .claude/skills 漏改等），证明此规则在实践中无法稳定执行。

### B. 全部 6 STANDARDs 都触发 archive ceremony（更严格 cite-by-vintage）

内容：Meta v2.1 archive + Code_Side v1.1 archive + Agent_Side v1.1 archive + HITL_Prompt v1.0 archive + Commit_Message v1.0 archive + GitHub_Markdown v1.0 archive，对应 6 个新 archive 文件。

**拒绝原因**：(a) 增加 PR 体量 +5 archive 文件；(b) mj-system v5.2 先例不支持（mj-system 仅 framework 文件触发 archive，其他 STANDARDs rename only）；(c) cite-by-vintage 对 5 个 STANDARDs（depth-of-detail rules）收益较低；(d) git history 通过 git mv 保留，不影响历史溯源。

### C. 仅 active 重命名，不动 archive 命名风格

内容：6 active rename + 不引入新 archive；现有 5 archive 文件保留当前 `_v1.0` / `_v1.1` / `_v2.0` 命名风格（无 `[DEPRECATED]_` 前缀；不加 `archived` / `replaced-by` 字段）。

**接受**（Phase C-1a 即此方案）：Phase C-1b（PR-3）将统一所有 archived 文件命名风格 + frontmatter（ADR-019）。本 PR 严格限定在 active 路径稳定化。

### D. 一并落 archive `[DEPRECATED]_` 前缀（合 Phase C-1b 进 Phase C-1a）

内容：rename + archive prefix + archived/replaced-by frontmatter 一次性 6 active + 6 archive 同 PR。

**拒绝原因**：用户 2026-05-09 决策 5 选 A（默认）；保持 Phase C-1a / C-1b 解耦降 PR 体量；Phase C-1a 已是 ~85 文件 PR，再加 archive 命名规范化会进一步增 ~50 wikilink 级联。

### E. 推迟到 v3.0 实施（不在 minor bump 期间反转）

内容：保持 v2.x 系列下 ADR-011 §4.2 active；待 v3.0（major bump）时一次性引入 stable path。

**拒绝原因**：(a) v3.0 时间未定，audit 痛点持续累积；(b) Phase C-2 ADR-017 §5.9 trigger #1 框架大版本升级判定；v3.0 更应聚焦内容大改而非仅命名规则；(c) mj-system v5.2 也是在 minor bump（v5.1 → v5.2）期间引入；先例支持。

## References

- 派生源：[mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md §4.1](https://github.com/MJ-AgentLab/mj-system/blob/develop/docs/rule/%5BSTANDARD%5D_Documentation_Management_Framework.md) lines 292-308 + §4.2 lines 320-327 + changelog 2026-05-05
- Partial supersede：[[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §4.2 filename rule + §5.6.2 file-move-step
- 落地：[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §4.4（本 ADR 同步落 STANDARD 文）
- 关联 ADR：
  - [[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]] §5.9（trigger #4 改名；本 PR Meta archive ceremony 部分触发；本 ADR-018 §Decision 子条款 §4.4.4 解决 rename 解读）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §Context（v2.0 → v2.1 三轨决策；不冲突）
  - [[../adr/[ADR]_015_HITL_Prompt_v1_0_Derivation|ADR-015]] §References（mj-system 派生先例；不冲突）
- 私有评估：用户 2026-05-08 brainstorming + 2026-05-09 三步序列选定（C → A → B）+ HITL Gate 1 批准（Phase C-1a Stage 5）
- 关联 GitHub Issue：[#78](https://github.com/MJ-AgentLab/mj-agent/issues/78)
- 后续 ADR-019（Phase C-1b）：archive `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter（细化 ADR-011 §5.6.2 archive 命名规则）
