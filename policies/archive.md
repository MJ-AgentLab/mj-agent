---
type: policy
artifact: archive
state: active
version: 1.0
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-23
track: shared
ai_visibility: source-of-truth
---

# Policy: Archive

> **Kernel home note (M6 PR4a-2)**: 本 policy 是**归档治理**的 kernel 真相源。它收纳了
> 归档触发量化（Meta §5.9）、active canonical 路径稳定原则（Meta §4.4）、STANDARD 整体
> 归档 ceremony（[[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6）、
> `archive.yml` manifest schema + G11/G12/G14/G15 门禁语义（锚定 M5 真实 validator
> `scripts/sdd/check_archive_manifest.py` / `check_archived_references.py`）、retention 与
> ai_visibility 规则。这些规则的 canonical home **自本 policy 起**就是这里。
>
> 在 M6 PR4 archive ceremony 落地前，源 STANDARD（Meta §4.4/§5.9）仍 `state: active` 留在
> `docs/rule/` 作为**历史源**；PR4 把 tri-track STANDARD 整体迁入 `archive/rule/`（§4 playbook）。
>
> **联动（cross-ref，不重复 port）**：
> - 文档治理门禁 A1-A6 / 12 类分类 / `track` 字段 → [[policies/documentation|policies/documentation]]
>   （其 §2.5 拆分阈值 + 头注 archive-trigger/path-stability 反向指入本 policy §1）
> - working 文档（`plans/**`）4 态机（`active/completed/archived`）→ [[sdd/lifecycle|sdd/lifecycle]]
>   §2；本 policy §8 仅落 `archived` 物理归档实施指引
> - capability package 归档流程 → [[sdd/workflows/archive-capability|sdd/workflows/archive-capability]]；本 policy 是其元规则
> - 门禁清单（G11/G12/G14/G15 等）总表 → [[sdd/gates|sdd/gates]]
> - 历史决策（DEPRECATED，按编号 prose 引用，不 wikilink）：ADR-017（归档触发量化）/ ADR-018
>   （路径稳定）/ ADR-019（archive 命名约定）/ ADR-021（working 文档生命周期）/ ADR-023
>   （陈旧文档 + plan GC infra）—— 均已 archive 至 `archive/decisions/superseded/`，决策已沉淀入本 policy。

## §1 归档触发判定与路径稳定原则

> 源：Meta §5.9（归档触发；ADR-017 决议）+ §4.4（active canonical 路径稳定；ADR-018 决议）。
> documentation.md §2.5 拆分阈值 + 头注 archive-trigger 反向指入本节。

### §1.1 归档触发判定（量化）

是否执行 archive ceremony 由以下 4 类**必触发** + 1 类**不触发**显式判定（reviewer 在 PR review
阶段对照本表 cite）：

| 触发归档？ | 场景 | 说明 |
|---|---|---|
| ✅ 是 | **框架大版本升级** | 如 Meta v2.x → v3.0；trio 整体演进 |
| ✅ 是 | **STANDARD 结构性重构** | 如章节模板换代（12 章 → 5 章）；归档名加 `_pre_<新版本>` |
| ✅ 是 | **70%+ 内容改写**（量化阈值） | 衡量原文 ≥ 70% 文本被替换 |
| ✅ 是 | **拆分 / 合并 / 改名** | 1 doc → N doc；N doc → 1 doc；scope / 命名重定义。**注**：drop `_vX.Y` 后缀的 rename 视为 rule application（§1.2.4），**非**本触发 |
| ❌ 否 | 小修小补、patch 升级、字段补充、typo / 链接修 | → git 历史承担；不进归档目录 |

- **判定优先级**：4 类必触发按 (1)→(2)→(3)→(4) 顺序短路判定（满足任一即触发）。
- **反例边界**：单段加新内容、§ 加新类目、§ 加新生命周期阶段，均属**字段补充**（❌ 否）。仅当
  **整文档结构** / **规则枚举集合** / **filename / scope** 发生变化时才升级触发。
- **HITL 入口**：判定结果直接喂 [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]]
  §5.6.1 HITL trigger；归档是 HITL 动作（git branch + PR review，A3 模式），不自动执行。

### §1.2 Active canonical 路径稳定原则

1. **主条款**：active canonical 文件名**默认不带 `_vX.Y` 后缀**；保持稳定路径。语义版本写在
   frontmatter `version` 字段 + 正文版本说明，不写进文件名。
2. **例外**：仅"多 active 主版本确需并存"（如 v1/v2 API 长期共存的 STANDARD）才允许文件名加
   `_vX.Y` 区分；例外而非默认。
3. **Legacy 反向规则**：归档文件**必须**保留 `_vX.Y` 或 `_pre_vX.Y` 后缀（cite-by-vintage）。
   与 §4 ceremony 的"version pin"一致。
4. **rename 解读子规则**：drop `_vX.Y` 后缀的 rename 视为 **rule application**（首次应用主条款），
   **非** §1.1 触发 #4 "改名"。仅当 STANDARD **同时**发生 substantive content evolution 时才触发
   archive ceremony（先例：框架文件 archive；其他 STANDARDs rename only）。

## §2 文档状态与归档生命周期

canonical 文档的退役沿 `active → deprecated → frozen → archived` 推进（归档时保留原 `track` 字段
值，含 `engineering-workflow`；living/frozen 引用判断不受 track 影响）：

| 状态 | 含义 | 触发 |
|---|---|---|
| `deprecated` | 显式宣告弃用 | 正式版本演进（§1.1）；ADR 决议 + HITL Gate；引用按 Living/Frozen 处理（§4） |
| `frozen` | 不再修改但保历史 | `deprecated` 后内容冻结；作 cite-by-vintage 快照 |
| `archived` | 物理迁入 `archive/<type>/` | ceremony（§4，canonical 文档）或 GC（§8，working 文档） |

> working 文档（`plans/**`）用**另一套** 4 态机（`draft/active/completed/archived`），语义是
> "任务完成"而非"被新版本替代"——见 [[sdd/lifecycle|sdd/lifecycle]] §2 + 本 policy §8。

## §3 archive.yml manifest schema（G11/G12）

> 锚定真实 validator `scripts/sdd/check_archive_manifest.py`（mirror `sdd/archive.schema.json`，
> 手写 PyYAML 校验，无 jsonschema 依赖）。本节是 schema 的权威说明；脚本是 ground truth。

每个 **archive unit**（`archive/**` 下携带归档内容的 leaf 目录）必须在其内容**同级**放一份
`archive.yml`。校验规则：

| 字段 | 必填 | 枚举 / 说明 |
|---|---|---|
| `archived_at` | ✅ | 归档日期 `YYYY-MM-DD` |
| `reason` | ✅ | 归档理由（自由文本；为何退役 + 现行替代去向） |
| `original_path` | ✅ | 归档前的原路径 |
| `ai_visibility` | ✅ | `hidden`（默认；AI 不应读取）\| `reference`（AI 可查阅历史背景）—— 见 §5 |
| `retention_class` | ✅ | `permanent` \| `5-year` \| `1-year` —— 见 §6 |
| `original_state` | ⬜（可选） | `draft` \| `active` \| `deprecated` \| `frozen`；填写时校验枚举 |

**FAIL 条件**：缺任一必填字段 / 枚举值非法 / 某 archive 子目录含 `.md` 内容文件但**无同级
`archive.yml`**（missing manifest）。`INDEX.md` 与 `.gitkeep` 不计为内容文件（不要求 manifest）。

真实范例（`archive/decisions/superseded/archive.yml`，M5-PR3b #217 落地）：

```yaml
archived_at: 2026-05-11
reason: "9 ADRs recording design decisions inherited from an upstream business system; ..."
original_path: docs/archive/adr/
original_state: deprecated
ai_visibility: reference
retention_class: permanent
related_decisions:
  - decisions/ADR-031_Spec_Anchored_Refactor.md
```

> `related_decisions` 等额外字段允许存在（脚本只校验必填 + 枚举，不禁止 extra key）。
> `archive/INDEX.md` 由 `scripts/sdd/generate_archive_index.py` 生成，**不**需要 archive.yml。

## §4 STANDARD 整体归档 ceremony（playbook）

> documentation.md 头注 + L22 反向指入本节。源：[[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]]
> §5.6（§4.2 filename + §5.6.2 file-move 已被 ADR-018 partial supersede；§5.6.1 HITL trigger /
> §5.6.3 目录语义 / §5.6.4 Living-vs-Frozen 仍有效）。M6 PR4 将按本 playbook 执行 tri-track
> STANDARD 归档。

**前置**：§1.1 判定触发 + HITL（PR review）确认。

1. **迁移**：`git mv` 旧 STANDARD → `archive/rule/`，文件名加 `[DEPRECATED]_` 前缀（ADR-019 命名
   约定）+ 保留 / 补 `_vX.Y` 版本后缀（§1.2.3 legacy 反向规则；cite-by-vintage）。
2. **状态翻转**：归档副本 frontmatter `state: active → deprecated`；正文顶部加 banner 指向 kernel
   后继（[[policies/documentation|policies/documentation]] / 本 policy）+ 触发 ADR。
3. **引用审计（corpus-wide）**：全仓 grep 旧 STANDARD 引用，逐条判 **Living vs Frozen**：
   - **Living**（"当前规则"语境）→ 重指 kernel home（doc 治理→`policies/documentation`；归档治理→本 policy）。
   - **Frozen**（ADR / ASSESSMENT 里"事故/决策时规则状态"语境）→ pin 到 archive 副本的
     `_vX.Y` 路径，措辞作 immutable artifact 保留。
   - **必须覆盖项目根 5 文件**（`README.md` / `CONTRIBUTING.md` / `CHANGELOG.md` / `GLOSSARY.md` /
     `CLAUDE.md`）+ **`AGENTS.md` 全部 5 件**（AI agent 指令契约——根 + 4 嵌套
     `capabilities|docker|src/mj_agent|tests`，per documentation.md §2.6 / ADR-035/036）：它们
     gate-light（§2.6 豁免 A1-A3），G14/G15 自动化扫描的根目录文件仅 `CLAUDE.md`（§5.2 扫描范围；
     嵌套 `AGENTS.md` 中 `tests/AGENTS.md` 亦在 walk 域外），其余的 living 引用**只能靠本步人工
     grep 兜底**。M6 三轨归档时 `GLOSSARY.md` 即因漏入本步 sweep 而留下指向 `docs/rule/` 的悬空
     链接——故此处显式点名。
4. **manifest + 墓碑**：在 `archive/rule/` 写 `archive.yml`（§3 五必填）+ `TOMBSTONE.md`（人读的
   迁移说明）。
5. **索引重建**：跑 `scripts/sdd/generate_archive_index.py` 刷 `archive/INDEX.md`；同步
   `docs/INDEX.md` Living 引用。
6. **forward-ref 清零**：解决 PR4 前 G14/G15 的 ~47 条 forward-ref WARN（指向尚未建的
   `archive/rule/` 等子树；建树后由 §3/§5 规则转为 PASS 或显式 `ai_visibility=reference`）。
7. **门禁 BLOCKING 翻转**：`archive/rule/` + manifest 就位且 forward-ref 清零后，`ci.yml` 把
   G11/G12/G14/G15 的 `continue-on-error: true → false`。**此翻转是 HITL/owner 动作**
   （`ci-blocking-gate-toggle` 门），不在 authoring PR 内单方执行。

> **先例（dogfood）**：M5-PR3b（#217）已按本 playbook 把 9 个 deprecated ADR 归入
> `archive/decisions/superseded/`（archive.yml + TOMBSTONE + INDEX）——证明流程闭环。

## §5 ai_visibility 与 archived-references 规则（G14/G15）

> 锚定真实 validator `scripts/sdd/check_archived_references.py`。

### §5.1 ai_visibility 二值

| 值 | 含义 |
|---|---|
| `hidden`（默认） | AI 不应读取（superseded STANDARD 等"不能当作当前事实"的内容） |
| `reference` | AI 可查阅历史背景（deprecated ADR 等"了解决策历史"的内容） |

### §5.2 active 文件引用 archive/ 路径的规则

扫描范围：`docs/`、`capabilities/`、`sdd/`、`policies/`、`decisions/`、`plans/` + `CLAUDE.md`
（`archive/` 树本身**不**扫描）。对每处字面 `archive/<path>` 引用（正则
`(?<![\w./-])archive/([\w./\-\[\]]+)`，**只匹配顶层 `archive/`，不匹配 `docs/archive/`**），
解析该引用所属 archive unit 的 `archive.yml`（向上就近查找）的 `ai_visibility`：

active 文件引用 `archive/` 路径**仅在以下任一成立时合法**，否则 WARN（M5 为 WARNING；PR4 后
BLOCKING）：

1. 目标 unit 的 `archive.yml` `ai_visibility: reference`，**或**
2. 引用文件在 allowlist `{CHANGELOG.md}`，**或**
3. 引用行带显式 `ai_visibility=reference` 行级标记。

> 因此：active 文档若需引历史归档内容，应引 `ai_visibility: reference` 的 unit（如
> `archive/decisions/superseded/`），或对 `hidden` unit 改用 git 历史 / 编号 prose 引用。

## §6 retention_class

| 类别 | 保留期 | 适用 |
|---|---|---|
| `permanent` | 不可删 | 重大 ADR / 历史 framework / 合规相关 |
| `5-year` | 5 年后 purge-eligible | 一般 capability / runbook |
| `1-year` | 1 年后 purge-eligible | working plan / 临时 evidence |

> retention 到期 → purge-eligible 检测 + 物理删除流程属 GC 范畴（Phase D+）；本 policy 只定义
> 类别语义。working 文档的 GC 触发见 §8。

## §7 archive/ 目录布局

顶层 `archive/`（SDD 重构引入）按"原 subdir 镜像 + 归档类型"组织；与 pre-SDD 的 `docs/archive/`
区分（后者内容由 ceremony 逐步并入顶层 `archive/`）：

| 路径 | 内容 | 状态 |
|---|---|---|
| `archive/decisions/superseded/` | 9 个 deprecated ADR（`[DEPRECATED]_[ADR]_*`） | ✅ M5-PR3b #217；`ai_visibility: reference` |
| `archive/rule/` | tri-track STANDARD 归档（`[DEPRECATED]_[STANDARD]_*_vX.Y`） | 🔜 M6 PR4（§4 playbook） |
| `archive/legacy/` | `docs/archive/` 历史材料并入 | 🔜 M6 |
| `archive/capabilities/` | deprecated capability package | 🔜 按需 |
| `archive/INDEX.md` | 全 archive 索引 | 由 `generate_archive_index.py` 生成 |

> 每个携内容的 leaf 目录必须带 `archive.yml`（§3）。`archive/` 引用合法性由 G14/G15（§5）裁决；
> archive NEEDLES 由 `check_wikilinks.py` 零维护 auto-discover（ADR-020 决议）。

## §8 working 文档物理归档（plans/ GC）

> working 文档（`plans/**`）的 `archived` 物理归档实施指引（落实 Meta §5.11.5 / ADR-021
> follow-up）。state 机本身见 [[sdd/lifecycle|sdd/lifecycle]] §2。

**触发条件**（三者皆满足）：`state: completed` 持续 ≥ 6 个月（180 天）+ 全仓 grep ref count = 0 +
HITL 人工 review 确认（**不自动跑 GC**）。

**操作流程**：

1. 跑 `scripts/find_old_completed_plans.py` 获候选清单；
2. 人工 grep 验证每个候选的引用计数（避免误删 active 引用）；
3. 首次 GC 时创建 `plans/archive/`（不预建空目录）；
4. `git mv plans/<name>.md plans/archive/<name>.md`；
5. frontmatter `state: completed → archived` + 加 `archived: <YYYY-MM-DD>`；
6. archived 文件**不更新**内部 wikilinks（frozen snapshot 原则；与 ADR-019 一致）；
7. `plans/` 不入 INDEX（不更新 `docs/INDEX.md`）；CHANGELOG 可记 GC 操作条目。

> 当前（2026-06）mj-agent `plans/` 最早 completed 文件距 6 月阈值未到；本节为指引，首次 GC 约 2026-11+。

## §9 与 SDD Workflows / 其他 policy 联动

| 对象 | 关系 |
|---|---|
| [[sdd/workflows/archive-capability|sdd/workflows/archive-capability]] | capability package 归档**流程**；本 policy 是其元规则（触发判定 §1 / manifest §3 / 可见性 §5 通用） |
| [[sdd/lifecycle|sdd/lifecycle]] | canonical 的 `deprecated` 与 working 的 `completed/archived` 状态来源；本 policy §2/§8 落归档侧实施 |
| [[policies/documentation|policies/documentation]] | §2.5 拆分阈值 → 本 policy §1.1 trigger #4；A1-A6 文档卫生门禁与 G11/G12/G14/G15 归档门禁互补 |
| [[sdd/gates|sdd/gates]] | G11/G12/G14/G15 门禁定义总表；本 policy 给其语义与 ceremony 上下文 |

---

> *M6 PR4a-2 — kernel home for archive governance（触发判定 + 路径稳定 / 状态机 / archive.yml
> manifest schema / ceremony playbook / ai_visibility + G14/G15 / retention / 目录布局 / working
> 文档 GC）。源 STANDARD（Meta §4.4/§5.9）在 PR4 archive 前留作历史源；门禁 BLOCKING 翻转见 §4 步骤 7。*
