---
type: assessment
domain: WORKFLOW
summary: >-
  对 Matt Pocock 公开 skills 仓 engineering(14)+productivity(5)=19 技能的哲学思想做深度调研，
  评估哪些可被 mj-agent 的 Claude Code 开发 workflows（Track-C 工程编排 + kernel）吸收采纳、哪些不需要，
  以及采纳前后的显著差异。结论：两套体系互补——mj-agent 强在「治理外壳」、Matt 强在「内核工艺」；
  只借「内核工艺纪律」思路、按 mj-agent native 规范承载；治理/编排类一律不引入（已有更严等价物）。
  判定分布（合计 19）：ADOPT 4（grilling / diagnosing-bugs / resolving-merge-conflicts / writing-great-skills）
  + ADAPT 8（4 项进实施草案：grill-with-docs / tdd / domain-modeling / to-issues；4 项仅登记低优先：
  codebase-design / improve-codebase-architecture / ask-matt / handoff）+ COVERED 3 + REJECT 4。
  §六 3.1-3.6 roadmap 已全部实施（PR #260-#264，2026-06-22），见正文「实施结局」。
tags:
  - assessment
  - workflow
  - skill-adoption
  - mattpocock
aliases:
  - mattpocock-skills Adoption Assessment
  - Matt Pocock 技能采纳评估
created: 2026-06-21
updated: 2026-06-22
state: active
version: v1.0
track: shared
owner: ranzuozhou
dimensions:
  - philosophy
  - adopt-verdict
  - before-after
period: 2026-06-21
---

# mattpocock/skills（engineering + productivity）→ mj-agent CC 开发 workflows 采纳评估

> **状态**：`active`（2026-06-22 由 vault 草稿经 `/mj-agent-doc-author` 升格入仓；`evidence/` 在 frontmatter SCAN_ROOTS 外，frontmatter / 引用已手动核验）。§一–七为升格时**保留的点-in-time 调研结论**，未因实施回改；roadmap 实施结局见下。

## 实施结局（2026-06-22，升格时追加）

本评估 §六 3.1–3.6 实施方案经 owner 拍板后**全部落地**，5 个 PR（均 `--base develop`，CI 全绿，owner 直合）：

| Phase | 项 | PR | 落点（实测） |
| --- | --- | --- | --- |
| P0 | 3.1 writing-great-skills | #260 | 新建 `docs/rule/[STANDARD]_MJ_Agent_Skill_Authoring_Craft.md`（v1.0）+ `sdd/adapters/{claude-code-skill,runtime-skill}.md` §Standards 指针（v0.3→0.4）+ INDEX |
| P1 | 3.2 grilling | #261 | `mj-agent-flow-intake` Step 2b 逼问纪律 + `mj-agent-flow-plan` 逼问回流 |
| P1 | 3.3 diagnosing-bugs | #262 | 新建 `.claude/skills/mj-agent-flow-diagnose/`（flow 第 10）+ flow-implement 3b 委派 + execution-loop §4.1 + INDEX |
| P1 | 3.4 resolving-merge-conflicts | #263 | `mj-agent-git-sync` §H2a 按意图解冲突 + git-check-merge cross-ref |
| P2 | 3.5 + 3.6 | #264 | flow-plan Step 2 纵切 + Step 5 seam-first / flow-intake Step 2c 主动锐化 / git-issue 纵切片 / doc-author ADR 开列判据 |

**与 §六 草案的实测偏差（evidence）**：
- **分支/提交类型**——§六草案写「新建 skill = feature/infra、改 skill body = maintain/infra」，实测 **`.claude/skills` 改动全部按项目实际约定走 `documentation/*` + `docs`**（git-commit skill 表 + PR-B1 先例为准；code/convention 覆盖草案假设）。
- **3.4 native 适配**——借鉴的「never `--abort`」与 mj-agent HITL 安全出口冲突 → 重构为「AI 默认解到底、不主动 `--abort`；`--abort` 保留 user-only 安全阀」。
- **P2 打包**——3.5/3.6 都改 flow-plan，独立 PR 会互相 rebase 冲突 → 合并为单 PR #264。
- **ADR-016 计数**——flow family 9→10（flow-diagnose）；on-disk 计数 35（>ADR-016 目标态 32，含 2 项先存 drift）→ ADR-016 加补记、INDEX 指向 contract check 为权威计数。
- 每项 body 改写均 **dogfood** `[STANDARD]_MJ_Agent_Skill_Authoring_Craft`（leading words / checkable 判据 / no-op 剪枝 / 单一真相源）。

剩余 **P3 低优先**（codebase-design 词汇 / ask-matt router / handoff 脱敏 / 架构卫生 ASSESSMENT，§三末列「不在 3.1-3.6 范围」）+ 零散 M-FU 仍 owner discretion。

## Context（背景与中心论点）

**触发**：用 `/deep-research`（ultracode）深度调研 Matt Pocock 公开 skills 仓
`engineering`（14 个技能）+ `productivity`（5 个技能）共 **19 个技能**的哲学思想，评估哪些可被
mj-agent 的 Claude Code 开发 workflows 吸收采纳、哪些不需要，以及采纳前后的显著差异。

**已完成调研**（只读，引用见末尾）：逐技能抓取 `SKILL.md` 原文 + 两份 README + 顶层 README +
元技能 `writing-great-skills`，并行 Explore 内部映射了 mj-agent 的 Track-C 工作流面
（`.claude/skills/` 34 技能 / `policies/` + `sdd/` kernel / 17-stage HITL execution-loop / 三轨治理）。

**中心论点（贯穿全文）**：两套体系处于**不同体裁**，恰好互补——

- **mj-agent 强在"治理外壳"**：HITL 必停拍板、三轨（A 代码 / B agent / C 工程编排）分离、
  doc lifecycle + archive ceremony、evidence-before-assertion、worktree 隔离、frontmatter/CI 门。
  回答的是 **谁拍板、何时停、如何留痕**。
- **Matt 的技能强在"内核工艺"**：把 vague 需求逼问清楚（grilling）、系统化排障
  （diagnosing-bugs）、深模块/缝（codebase-design）、behavior-first 测试（tdd）、垂直切片拆活
  （to-issues）、按意图解冲突（resolving-merge-conflicts），以及**写技能本身的工艺**
  （writing-great-skills）。回答的是 **循环内部怎么想、怎么做**。

→ **mj-agent 的循环外壳已很完备，但循环内部的"工程思维纪律"偏隐性/临场**。Matt 的技能正好补在
这里。所以结论不是"照搬一套框架"（会与 mj-agent 既有治理冲突），而是
**借"内核工艺纪律"的思路，按 mj-agent 原生规范承载；治理/编排类一律不引入（已有更严的等价物）**。

**两条硬约束（来自项目 feedback memory，全程遵守）**：
1. **跨项目借鉴边界**：只借"问题识别 + 思路"，具体方案（结构/字段/术语/落点）按 mj-agent native
   设计——**不 mirror Matt 的 `SKILL.md`/`CONTEXT.md` 模板**。
2. **两类 skill 严格区分 + HITL**：采纳目标是 `.claude/skills/`（Track C 工程编排，ADR-013 2-field）
   与 kernel 工作流文档，**不是** `src/mj_agent/skills/` 运行时业务技能。`.claude/**` 改动在交互模式
   须逐写**拍板**；技能/文档 authoring 用 **single-agent + 自验**（非 rigid-schema workflow）。

---

## 一、两套哲学的对照

| 维度 | Matt Pocock "Skills For Real Engineers" | mj-agent SDD kernel |
| --- | --- | --- |
| 体裁 | 模块化、**可个性化、反框架**（"adapt/compose/personalize"） | **强框架**：spec-anchored、三轨治理、必停拍板 |
| 目标失效面 | 4 类：愿景↔执行错位 / 啰嗦沟通 / 代码质量 / 架构腐化 | 进程漂移、silent agent 失败、文档失真、secret 泄漏 |
| 核心机制 | **grilling**（逼问）、`CONTEXT.md` ubiquitous language、deep module、TDD vertical slice、tracer-bullet issue | 17-stage HITL loop、propose→拍板→apply、frontmatter/CI 门、archive ceremony |
| 重心 | 循环**内部的工艺/认知纪律** | 循环**外部的治理/编排/留痕** |
| 元层 | `writing-great-skills`：predictability 为根德性，context-load vs cognitive-load，leading words，progressive disclosure，五大失效模式 | ADR-013/016 schema、doc 12-type taxonomy、A1-A14 门 |
| 文化 | 轻量、临场、英文、单人/小团队 | 重治理、留痕、中文、SDD |

**关键张力（采纳时必须吸收的"代价"）**：Matt 的纪律一旦套进 mj-agent 的治理外壳，会**获得严谨性
但失去 Matt 式的轻量自发性**（变成被 gate、被留痕、被 track）。这是采纳后必然的性格变化，不是 bug。

---

## 二、逐技能评估总表（19 个）

判定口径：**ADOPT**=填真空缺、低冲突，值得原生承载；**ADAPT**=借思路融入既有面，不独立成件；
**COVERED**=mj-agent 已有更严等价物；**REJECT/低**=冲突/越界/前提不成立。

| # | 技能 | 类/触发 | 哲学一句话 | 判定 | mj-agent 承载面 |
| --- | --- | --- | --- | --- | --- |
| 1 | **grilling** | prod / model | 一次一问、带"推荐答案"锚点的 relentless 逼问，build 前逼出隐藏假设 | **ADOPT** | flow-intake/flow-plan 增强（Stage 0/4） |
| 2 | grill-me | prod / user | grilling 的 user-invoked 包装 | COVERED→随 1 | （随 grilling 触发） |
| 3 | grill-with-docs | eng / user | grilling + domain-modeling，边问边出 glossary/ADR | ADAPT | flow-plan ↔ doc-author 联动 |
| 4 | **diagnosing-bugs** | eng / model | **先建 tight/red-capable/deterministic feedback loop 再谈假设**；最小化复现；排序可证伪假设；先回归测试后修；事后"什么能预防它" | **ADOPT** | 新 `flow-diagnose` 或 flow-verify 增强 |
| 5 | tdd | eng / model | behavior-first、走 public interface、vertical slice red-green、"测试读起来像规格" | ADAPT（部分 COVERED） | flow-implement 原则强化（Track A 纯码） |
| 6 | codebase-design | eng / model | deep module / seam / deletion-test 共享词汇 | ADAPT（低） | code-review/设计讨论词汇 |
| 7 | domain-modeling | eng / model | **主动**锐化 ubiquitous language，inline 即时更新 glossary，仅对难逆决策开 ADR | ADAPT | 既有 glossary/ADR/biz_catalog 纪律强化 |
| 8 | implement | eng / user | 结构化执行：TDD@seam + 常 typecheck + 分层测试 + review 后 commit | COVERED | flow-implement/verify/self-review 已更严 |
| 9 | prototype | eng / user | throwaway code 回答**一个**问题（TUI 逻辑原型 / UI 多变体） | REJECT（低） | 后端 data-agent，无 UI 迭代文化 |
| 10 | improve-codebase-architecture | eng / user | 持续架构扫描 + HTML 可视报告 + grill 选项 | ADAPT（低） | 可选 ASSESSMENT 活动 |
| 11 | ask-matt | eng / user | router over user-invoked 技能；flow graph 命名分支点；smart-zone token 管理 | ADAPT（低） | stage→skill map 已近似 |
| 12 | setup-matt-pocock-skills | eng / user | 一次性把该套件装配进仓（issue tracker/labels/doc 布局） | REJECT | 是该套件**安装器**，不适用 |
| 13 | **to-issues** | eng / user | 把 plan/PRD 拆成 **vertical-slice tracer-bullet** 独立可抓 issue；prefactoring | **ADAPT** | flow-plan/git-issue 的 PR 链拆分原则 |
| 14 | to-prd | eng / user | 综合对话成 PRD（不再访谈）+ testing-seam-first | COVERED + 小借鉴 | PLAN 文档已等价；借 seam-first |
| 15 | triage | eng / user | issue/PR 状态机 + verify-before-brief + AI 免责声明 | REJECT（低） | owner-driven、外部 PR 少 |
| 16 | **resolving-merge-conflicts** | eng / user | **按原始意图**解冲突（读 commit/PR/issue 找 why）、保留双方意图、文档化取舍、never `--abort`、跑全检查 | **ADOPT** | 新 git-* 技能 或 git-sync 增强 |
| 17 | handoff | prod / user | 压缩会话成 handoff doc：引用不复制、脱敏、suggested-skills、存 OS temp | ADAPT（低） | 已有 memory + vault；借脱敏/引用纪律 |
| 18 | teach | prod / user | 多会话 mission-grounded 教学、stateful 工作区、storage-strength | REJECT | dev workflow 外（已有 learn-kit 插件） |
| 19 | **writing-great-skills** | prod / user | **写技能的元哲学**：predictability 为根；context-load vs cognitive-load；信息阶梯 + progressive disclosure；leading words；五大失效模式（premature completion / duplication / sediment / sprawl / no-op） | **ADOPT（最高杠杆）** | doc-author + 一份"技能写作 STANDARD" + runtime-skill-doc-improve |

**采纳结论（按表内 19 行口径逐一计数）**：
- **ADOPT 4**：grilling、diagnosing-bugs、resolving-merge-conflicts、writing-great-skills（各有 §三 3.1–3.4 实施草案）。
- **ADAPT 8**（表中 8 行带 ADAPT 判定，分两档）：
  - *进入 §三 实施草案（4）*：grill-with-docs、tdd、domain-modeling、to-issues（落 §三 3.5/3.6 与 flow-implement）。
  - *仅登记、低优先（4，表内标「（低）」）*：codebase-design、improve-codebase-architecture、ask-matt、handoff（见 §三「其余低优先 ADAPT」）。
- **COVERED 3**：grill-me、implement、to-prd（mj-agent 已有更严等价物）。
- **REJECT 4**：prototype、setup-matt-pocock-skills、triage、teach（冲突/越界/前提不成立）。

合计 4 + 8 + 3 + 4 = **19**，与 §二 表逐行一致。

---

## 三、推荐采纳的核心纪律（深入 + 原生承载方案）

> 每条都给：**借什么思路 / 为何是真空缺 / mj-agent 原生怎么承载（不 mirror）/ 边界与 HITL 注意**。

### 3.1 writing-great-skills —— 最高杠杆（元层）

- **借什么**：predictability=根德性；description 只放触发分支（front-load leading word，一分支一句，删身体已有的身份）；
  信息阶梯（in-skill step → in-skill reference → external reference 经 context pointer）；
  **completion criterion 必须 checkable + exhaustive**（防 premature completion）；**leading words**（用预训练里的紧凑概念锚行为）；
  五大失效模式 + no-op 测试（"是否改变默认行为？否则删整句"）。
- **为何真空缺**：mj-agent 已有 ADR-013/016 *schema*（2-field、命名），但**没有"技能写作工艺质量"词汇**——
  现有 34 技能/运行时 SKILL.md 偏治理描述，未必按 leading-words/progressive-disclosure/no-op 剪枝优化。
- **原生承载**：新增一份 `docs/rule/[STANDARD]_Skill_Authoring_Craft.md`（或并入 `sdd/adapters/claude-code-skill.md`
  与 `runtime-skill.md` 的"body 质量"小节）：把上述工艺词汇 native 化为 mj-agent 的 authoring checklist，
  供 `mj-agent-doc-author` / `mj-agent-runtime-skill-doc-improve` / 评审引用。**杠杆最高**：一次落地改善整个技能生态
  （含两类 skill 的 body 质量）。
- **边界/HITL**：纯文档（Track C reference），交互模式拍板即可；single-agent authoring。
  与既有 schema 不冲突（schema 管"有哪些字段"，本条管"字段/正文写得好不好"）。

### 3.2 grilling —— relentless 逼问纪律

- **借什么**：**一次一问**（"asking multiple questions at once is bewildering"）+ 每问**附自己的推荐答案**做锚点
  （用户只需 同意/改正，而非从零回答）+ 沿"design tree"逐依赖下钻 + **能查代码就别臆测** + 直到 shared understanding 才停。
- **为何真空缺**：mj-agent 的 flow-intake/flow-plan 偏"repo-scan → 写 plan body"，**缺少 build 前对 vague 需求的主动
  逼问纪律**。AskUserQuestion 是离散选项，不等于连续逼问。
- **原生承载**：增强 `mj-agent-flow-intake`（Stage 0）/ `mj-agent-flow-plan`（Stage 4）的 SKILL body：加一段
  "Grilling discipline"——对**真歧义/新颖**任务，先做一次一问、推荐答案锚点的逼问，再进入 plan。
  落点与 mj-agent 的 AskUserQuestion "(Recommended) 首选项放第一" 惯例天然契合。
- **边界/HITL 校准（关键）**：必须与 mj-agent feedback「方向已明确就直接执行，别过度 gate」**对齐**——
  grilling 只对**前期真歧义**开，不对已定方向的执行加门；否则违反既有"别用仪式拦"的偏好。
  这是采纳成败点：**逼问 ≠ 执行门**。

### 3.3 diagnosing-bugs —— feedback-loop-first 排障

- **借什么**：**90% 在于先建一个会对"这个 bug"变红的 tight/deterministic loop**，再做 bisection/假设/插桩；
  最小化复现（每次砍一个元素）；3–5 条**可证伪**假设排序后再测；一次只动一个变量、`[DEBUG-uuid]` 标记便于清理；
  **先在正确缝写回归测试再修**；事后问"什么结构能预防它"。
- **为何真空缺**：mj-agent 无原生系统化排障工作流（superpowers:systematic-debugging 是外部通用件，非 native）。
  对 data-agent 尤其值：SQL 生成 / guardrail / LLM 行为类 bug 的"红信号"可直接映射到 **eval 谐波**。
- **原生承载**：新增 `mj-agent-flow-diagnose`（或并入 flow-verify 一节）。"tight pass/fail 信号"在本项目里
  常常 = 一条最小 pytest / 一次 `mj-agent check` / 一条最小 eval case。与 evidence-before-assertion 同源。
- **边界/HITL**：纯 Track C 编排技能；交互模式拍板新建。注意排障若触达 4 必停面（guardrail/precheck/prompt/catalog）
  的修复，仍走既有必停拍板，不被本技能绕过。

### 3.4 resolving-merge-conflicts —— 按意图解冲突

- **借什么**：解冲突先读 commit/PR/issue 找**每段改动的 why**；尽量**保留双方意图**，冲突时选"匹配本次 merge 目标"的
  那个并**文档化取舍**；**never invent 新行为**；**永远解、不 `--abort`**；完成前跑 typecheck/test/format 全套。
- **为何真空缺**：mj-agent 做 stacked-PR rebase 链（见 memory），但**无显式冲突解决纪律**。本条干净、低冲突、
  与 evidence-before-assertion + 留痕文化完美同构。
- **原生承载**：新增 `mj-agent-git-resolve-conflict`，或并入 `mj-agent-git-sync` 一节；"跑全检查"直接复用
  Level A 验证矩阵（ruff/mypy/pytest）。
- **边界/HITL**：Track C；交互模式拍板新建。

### 3.5 to-issues —— vertical-slice / tracer-bullet 拆活（ADAPT）

- **借什么**：把大 plan/milestone 拆成**端到端纵切**（穿透 schema/API/UI/测试的窄而完整路径），
  每片**自身可 demo/可验、可独立抓取**、按依赖顺序发布——而非按层水平切（后端→前端→测试）。
- **为何有用**：mj-agent 常做多 PR 链（4-PR 完成度审计链、5-PR 解耦链）。"独立可验纵切"框架能改进
  **milestone→PR 的拆分质量**。
- **原生承载**：把"纵切/tracer-bullet + prefactoring（make the change easy, then make the easy change）"
  作为原则写入 `mj-agent-flow-plan` 的 PR 链拆分指引；issue 由既有 `mj-agent-git-issue` 创建（不引入新 tracker 概念）。
- **边界**：mj-agent issue/PR 体系已 native，**只借切分思路**，不借 Matt 的 issue 模板/标签体系。

### 3.6 domain-modeling / grill-with-docs —— 主动锐化 ubiquitous language（ADAPT）

- **借什么**：把领域建模当**主动纪律**——临场挑战术语、用具体边界场景压测、术语一旦定下**立即** inline 更新词典，
  仅对"难逆 + 反直觉 + 真权衡"的决策开 ADR；边 grilling 边产出文档（doc 是并行交付物，非事后补）。
- **为何 ADAPT 而非 ADOPT**：mj-agent **已有等价物且更分布式**——`docs/glossary/upstream_business_warehouse.md`、
  `decisions/` ADR、`biz_catalog/qcm_catalog.yaml`（镜像上游数据字典）、`INDEX.md`。Matt 的**单一 `CONTEXT.md`
  与 mj-agent 分布式 doc 治理冲突**，**不引入 CONTEXT.md**。
- **原生承载**：把"主动锐化 + 场景压测 + inline 更新"的*纪律*写进 `mj-agent-flow-plan` / `mj-agent-doc-author`，
  挂到既有 glossary/ADR/catalog 工件上。注意领域语言与上游仓存在跨仓边界（attribution → glossary 元文档）。

### 其余低优先 ADAPT（仅登记，不优先）

- **codebase-design**：deep module / seam / deletion-test **词汇**可丰富 code-review；mj-agent 是 MVP 期小码基，
  非重模块设计阶段——只借词汇，不立件。
- **ask-matt（router）**：34 技能确有 cognitive load；但 mj-agent 多为 model-invoked 自动发现 + execution-loop
  的 stage→skill map 已近似 router。可选加一个极轻量"哪个 flow"导引，低优先。
- **handoff**：mj-agent 已有更丰富的**持久 memory（MEMORY.md + 单事实文件）+ vault**。只借"引用不复制 + 脱敏"
  纪律（与 secrets 治理同源）；不新建 handoff 机制。
- **improve-codebase-architecture**：HTML 报告机制偏重；只借"周期性架构卫生扫描"作可选 ASSESSMENT。

---

## 四、不采纳 / 不需要（含理由）

| 技能 | 不采纳理由 |
| --- | --- |
| **implement** | mj-agent 的 flow-implement(8)+flow-verify(10)+flow-self-review(11)+git-commit 已是**更严**版本（11 项自检 + HITL 门）。Matt 版是其子集。 |
| **prototype** | 后端 data-agent，无 UI 多变体迭代文化；逻辑 throwaway harness 思路已被 diagnosing-bugs 的"throwaway loop"覆盖。 |
| **setup-matt-pocock-skills** | 它是**该套件的安装器**（配 issue tracker/labels/doc 布局）；mj-agent 已 native 配齐，不适用。 |
| **triage** | 前提是活跃多贡献者 tracker + 大量外部 PR；mj-agent 是 owner-driven、0-review 直合，前提不成立。"AI 评论加免责声明"可零成本借。 |
| **teach** | 面向"教人类学概念"，在 dev workflow 之外；该需求已有 learn-kit 插件承载。 |
| grill-me | 仅是 grilling 的调用别名，随 grilling 采纳即覆盖。 |

---

## 五、采纳前后的显著差异（before / after）

| 纪律 | 采纳前（现状） | 采纳后（显著不同） |
| --- | --- | --- |
| **技能/文档写作（writing-great-skills）** | 按 schema 校验"字段齐不齐"；body 质量靠个人手感，易 sediment/sprawl/no-op 堆积 | 有 native 工艺词汇与 checklist：description 只留触发分支、completion criterion 可检可穷尽、leading words 锚行为、no-op 剪枝——**整个技能生态可预测性↑、token/维护成本↓** |
| **前期需求（grilling）** | flow-intake/plan 偏 repo-scan→写 plan；隐藏假设常到实现期才暴露 | 对真歧义任务先做一次一问 + 推荐答案锚点逼问——**返工↓、scope drift↓**；且**严格区分逼问 ≠ 执行门**，不破坏"方向明确就执行" |
| **排障（diagnosing-bugs）** | 临场 debug，易直接跳假设、无 deterministic 红信号 | 先建会变红的 tight loop 再下钻；先回归测试后修；事后做预防归因——**复现可靠性↑、误修↓、回归网↑**，与 eval 谐波打通 |
| **解冲突（resolving-merge-conflicts）** | stacked-PR rebase 链解冲突无显式纪律，易丢意图 | 按 commit/PR/issue 的 why 解、文档化取舍、完成前跑全检查——**意图保真↑、never `--abort`** |
| **拆活（to-issues 纵切）** | 多 PR 链按经验拆，偶有层间耦合 | 端到端 tracer-bullet 纵切、独立可验、依赖序发布——**PR 可独立 review/合、并行度↑** |
| **领域语言（domain-modeling）** | glossary/ADR/catalog 已有但更新偏被动/批量 | 主动挑战术语 + 场景压测 + inline 即时更新——**术语漂移↓**（仍挂既有分布式工件，不引入 CONTEXT.md） |

**总体差异**：采纳前 mj-agent = **强治理外壳 + 隐性内核工艺**；采纳后 = **强治理外壳 + 显式内核工艺纪律**，
且这些纪律被 mj-agent 的 HITL/留痕/track 外壳"硬化"（更严谨，但少了 Matt 式自发轻量——这是已知代价）。

---

## 六、3.1–3.6 具体实施方案（分级落地；本轮仅规划，不实现）

> **通用治理（每项都适用，不再重复）**：
> - **落点判定**：`.claude/skills/**` = 受保护路径 → 交互模式写入**逐弹权限 prompt = 拍板**（`allow` 不可抑制），AI 改 + commit；`sdd/`、`docs/rule/` 非受保护，走 Stage 6 doc HITL Gate。
> - **authoring 方式**：single-agent + 自验（**不**上 rigid-schema multi-agent workflow）。
> - **借鉴边界**：只借思路，结构/术语 native 化；**不引入** Matt 的 `CONTEXT.md`、issue 模板、setup 安装器。
> - **命名/schema**：新 skill 必须 `mj-agent-<group>-<verb>`（group ∈ {flow,git,doc,runtime,infra}），ADR-013 2-field；description ≥200 字 + `Do not use for:` 反向触发（A12 门）。
> - **必停不可绕**：任何方案若触达 4 必停面（guardrail/precheck/prompt/catalog）的修改，仍走 §3.1 必停拍板。
> - **分支/提交（policies/git-branching.md §4.2，均 `--base develop`，各起 worktree G1）**：新建 skill = `feature/*` + `infra`；改既有 skill body = `maintain/*` + `infra`；纯 docs（STANDARD/adapter）= `documentation/*` + `docs`。

### 【P0】3.1 writing-great-skills → 技能写作工艺 STANDARD + 两 adapter 挂钩

**落点**
- 新建 `docs/rule/[STANDARD]_MJ_Agent_Skill_Authoring_Craft.md`（单一真相源）。
- 改 `sdd/adapters/claude-code-skill.md` §Standards（v0.3→0.4）：加 `### §Standards.1a 技能正文工艺质量` 指针（不复制正文）。
- 改 `sdd/adapters/runtime-skill.md` §Standards（v0.3→0.4）：在 activation / 5-iteration 节旁加同款指针。

**STANDARD frontmatter（照 `docs/rule/[STANDARD]_GitHub_Markdown.md` 模子）**
```yaml
---
type: standard
domain: SKILL
summary: 定义 mj-agent 两类 skill（in-source runtime / in-tree workflow）正文与 description 的写作工艺质量准则——可预测性、双负载权衡、信息阶梯、leading words、失效模式诊断；是 ADR-013/016 schema 层之上的"正文质量层"
owner: ranzuozhou
created: 2026-06-21
updated: 2026-06-21
state: draft
version: v1.0
track: shared
tags: [standard, skill-authoring, documentation]
---
```

**正文章节草案（native 设计，借 writing-great-skills 概念但不抄其文本）**
1. **核心原则·可预测性为根德性** — skill 存在是从随机系统榨确定性；目标=agent 每轮走**相同 process**（非相同输出）。下列每条都服务可预测性（leading word「可预测性」）。
2. **双负载权衡（context-load vs cognitive-load）** — model-invoked（description 常驻 context、可自触发）vs user-invoked（零 context、靠人记）。mj-agent 在树 skill 默认 auto-discover（model-invoked）→ 准则：description 每词都增 context-load，须比 body 更狠剪枝。
3. **Description 工艺（强化既有 A12 ≥200 字 + 反向触发门）** — 前置 leading word；一触发分支一句，同义改写=duplication 须合并；删 body 已有的身份描述，只留触发词 + "另一 skill 需要时"的 reach 子句。
4. **信息阶梯 + 渐进披露** — in-skill step（有序动作）→ in-skill reference（按需查的规则）→ external reference（经 context pointer 推独立文件，命中才加载）；只有部分 branch 用到的内容下推（对照 runtime-skill bundled-resource 治理）。
5. **完成判据 checkable + exhaustive** — 每个 Step 以"可判定 done/not-done"判据结尾（"每个改动的 model 都已登记"而非"产出一个变更列表"），防 premature completion；判据 irreducibly 模糊且观察到抢跑时才 sequence-split 隐藏后续步骤。
6. **Leading words 词表** — 登记 mj-agent 已用 leading words：必停 / 拍板 / 风味(A/B/C) / Level(A/B/C) / 红信号 / 纵切 / 逼问，鼓励复用而非重述。
7. **五大失效模式 + no-op 测试** — premature completion / duplication / sediment / sprawl / no-op；no-op 测试：删这句是否改变默认行为？否则删整句。
8. **与既有治理的边界** — 本 STANDARD 治"正文写得好不好"；ADR-013/016 治"有哪些字段"；A12 治"description 最低门"；runtime-skill §Standards 治 6 段 body heads + activation。互补不重叠。

**集成锚点** — 被 `mj-agent-doc-author`（写 SKILL/STANDARD）、`mj-agent-runtime-skill-doc-improve`（改 runtime body）、`mj-agent-flow-self-review`（Stage 11）引用；两 adapter §Standards 以指针引用（单一真相源）；加入 `docs/INDEX.md`（A5）。

**治理** — `documentation/*` + `docs`；track shared（治 agent + engineering-workflow 两类 SKILL）；Stage 6 doc HITL Gate；A1/A2/A4/A5 适用，评估 A6（若进 CLAUDE.md doc-governance 指针清单则同步一行）。

**验证** — `python scripts/check_frontmatter.py` + `check_wikilinks.py` 通过；两 adapter 指针解析到新 STANDARD；INDEX 含新条目；对 1 个现有 skill 用新 checklist 走一遍，能挑出 ≥1 处 no-op/duplication。

### 【P1】3.2 grilling → flow-intake / flow-plan 加「逼问纪律」（不新建 skill）

**落点** — 改 `.claude/skills/mj-agent-flow-intake/SKILL.md`（Stage 0）+ `.claude/skills/mj-agent-flow-plan/SKILL.md`（Stage 4）body。

**改动形态** — flow-intake 在 `## Step 2: 澄清 scope / out-of-scope` 后插 `## Step 2b: Grilling 逼问纪律（仅前期真歧义）`；flow-plan 在 `## Step 1: Capture Context` 末加「逼问回流」cross-ref。

**Step 2b 草案（leading word「逼问」）**
- 触发：需求含**未决分支 / 新颖 / 真歧义**（非已定方向）。
- 纪律：**一次一问**（多问齐发令人迷失）；每问**附自己的推荐答案**做锚（对齐 mj-agent AskUserQuestion「(Recommended) 首选项放第一」）；沿 **design tree** 逐依赖下钻；**能查代码/glossary/catalog 就别臆测**；直到所有分支 resolved 或显式 defer 才停。
- **校准（关键，防违背「方向明确就执行」feedback）**：逼问 ≠ 执行门。仅前期歧义触发；方向已明确 → 直接进入 Step 3，不加门。离散单点决策用 AskUserQuestion 承载，连续逼问走对话。
- 完成判据：design-tree 每分支标 resolved / defer(M-FU)（checkable）。
- ❌ Anti-pattern：把逼问用于已定方向的执行段；一次抛多问；不给推荐答案空转。

**集成锚点** — Stage 0/4；与 `mj-agent-flow-scope-drift`（Stage 9）区分（逼问在前期定方向，scope-drift 在实现中查偏离）。

**治理** — `maintain/*` + `infra`；受保护路径逐写拍板；只动 2 个 flow skill body。

**验证** — 两 skill 触发词不变（仍可触发）；真歧义样例 dry-run 走一次一问 + 推荐答案；方向已明确样例确认**不**触发逼问（**负向测试**，防过度 gate）。

### 【P1】3.3 diagnosing-bugs → 新建 mj-agent-flow-diagnose

**落点** — 新建 `.claude/skills/mj-agent-flow-diagnose/SKILL.md`（flow 家族第 10 个）；并在 `mj-agent-flow-implement` 的 `## Step 3b: Root-cause-first` 加**委派**：硬 bug / 性能回归 / flaky → 调 `/mj-agent-flow-diagnose`（简单显见 bug 仍在 3b 内解决，避免与既有 3b 重叠）。

**frontmatter（2-field）**
```yaml
---
name: mj-agent-flow-diagnose
description: This skill runs mj-agent disciplined bug/performance diagnosis (feedback-loop-first) — build a tight red-capable deterministic signal BEFORE hypotheses, minimise repro, rank falsifiable hypotheses, instrument one variable, write the regression test at the right seam BEFORE fixing, then post-mortem "what structure would have prevented it". Make sure to use this skill whenever the user says "排查 bug", "复现", "diagnose", "debug this", "为什么失败", "性能回归", "perf regression", "flaky", "时好时坏", "查不出原因" in the mj-agent context. mj-agent red-signal maps to a minimal pytest case / `uv run mj-agent check` / a minimal eval case / a Studio repro. Do not use for: Stage 8 coding methodology incl. simple bug fixes (use mj-agent-flow-implement Step 3b), Stage 10 verification matrix (use mj-agent-flow-verify), or Stage 11 self-review (use mj-agent-flow-self-review). 触达 4 必停面（guardrail/precheck/prompt/catalog）的修复仍走 §3.1 必停拍板。
---
```

**body skeleton（house style：DOT digraph + bilingual + Step N + ❌ + Handoff）**
```
# mj-agent Flow — Diagnose (HITL Stage 8/10 邻接)
## Overview         （工作位置：bug/失败时被 flow-implement 3b 委派或直接触发）
## Workflow         （DOT digraph：建红信号→复现&最小化→排序假设→插桩→修+回归→清理&归因）
## When to Run This Skill   （MUST：硬 bug/perf/flaky；MAY skip：显见 typo bug；MUST NOT：当编码方法论）
## Step 1: 建"会变红"的反馈环（红信号）   （映射：最小 pytest / mj-agent check / 最小 eval / curl Studio / SQL repro / git bisect；越快越确定越好）
## Step 2: 复现并最小化   （每次砍一个元素，剩下的都 load-bearing）
## Step 3: 排序可证伪假设（3–5 条）   （每条："若 X 是因，改 Y 则消失 / 改 Z 则更糟"；展示给 user 可重排）
## Step 4: 插桩（一次一变量）   （debugger/REPL > 定向日志；[DEBUG-uuid] 标记便于清理）
## Step 5: 先在正确缝写回归测试，再修   （修后跑 Step 1 红信号转绿）
## Step 6: 清理 + 事后归因   （删 [DEBUG-*]；commit 写中选假设；问"什么结构能预防它"，结构性→立 follow-up）
## What This Skill DOES NOT DO
## Anti-patterns    （❌ 没建红信号就跳假设；❌ 一次动多变量；❌ 先修后补测试）
## Reference Files   （execution-loop §5 Level 矩阵；evidence-before-assertion）
## Handoff to mj-agent-flow-verify  （Stage 10 回归；结构性问题→flow-plan 立 follow-up）
```

**集成锚点** — execution-loop §4.1 skill map 加一行 flow-diagnose（Stage 8/10 邻接子纪律，**非新 stage**）；flow-implement 3b 委派；红信号 = evidence-before-assertion 的实证。

**治理** — `feature/*` + `infra`；新 skill 进 `.claude/skills/**` → 逐写拍板；ADR-016 命名 ✓（flow group）；A12 ✓；无 schema 变更 → 不需 ADR。

**验证** — auto-discover 触发（"flaky"命中本 skill、"开始编码"命中 flow-implement 不误命中）；拿一个真实历史 bug（如 #134 venv symlink 类）dry-run 走 6 步；description ≥200 字 + 含 `Do not use for:`。

### 【P1】3.4 resolving-merge-conflicts → 深化 git-sync §H2（不新建 skill）

**落点** — 改 `.claude/skills/mj-agent-git-sync/SKILL.md` 既有 `### H2 冲突解决流程`（git-sync 已拥有冲突解决场景，是天然归属）；从 `mj-agent-git-check-merge` cross-ref。**不新建 skill**（git 家族已 9 个）。

**H2 增补草案（leading word「按意图」）**
1. **先找 why**：每段冲突 hunk，读 commit message / 关联 PR / issue，弄清两侧改动各自**意图**（非只看语法）。
2. **保留双方意图**：能并存则并存；冲突时选**匹配本次 merge 目标**的一侧，commit body **文档化取舍**（哪侧、为何）。
3. **绝不发明**：只解既有冲突，不引入新行为。
4. **永远解、不 `--abort`**：承诺解完（含 rebase 链续到底）。
5. **续行前跑 Level A**：复用 §5 Level A 矩阵（`uv run ruff check` / `uv run mypy src/mj_agent` / `uv run pytest tests/unit`）确认绿，再 `--continue` / 提交。

**集成锚点** — git-sync Stage 13/17 侧循环；stacked-PR rebase 链（既有实践）冲突走此；Level A 直接引用 §5。

**治理** — `maintain/*` + `infra`；受保护路径拍板；只增补 H2 一节。

**验证** — 构造双侧改同文件的样例冲突，确认走"读 why→文档化取舍→Level A 转绿→续"；H1/H3–H8 不受影响。

### 【P2】3.5 to-issues 纵切 → flow-plan Step 2/5 + git-issue（含 to-prd seam-first）

**落点** — 改 `mj-agent-flow-plan` `## Step 2: Task Breakdown`（加纵切）+ `## Step 5: Verification Plan`（加 testing-seam-first）；从 `mj-agent-git-issue` cross-ref（issue 继承切片 AC + blocked-by 序）。**不引入新 tracker 概念**。

**草案**
- **Step 2 纵切优先（leading word「纵切」/ tracer-bullet）**：拆多 PR/issue 时，每片**端到端穿透相关层**（如新增一业务指标：catalog 条目→tool→guardrail 放行→eval case），**自身可验、可独立 review-合**，按 **blocked-by 依赖序**发布；先 **prefactoring**（make the change easy, then make the easy change）。❌ 水平切（先全 catalog→再全 tool→再全 test）。
- **Step 5 testing-seam-first（借 to-prd）**：拆活先定**测试缝**——优先复用既有缝，**最小化新缝（理想 1 个）**，缝放最高架构层；mj-agent 缝常=一条 eval / 一条 unit。

**集成锚点** — Stage 4 plan body；git-issue（Stage 1）按切片建 issue 带 AC + blocked-by；对接既有多 PR 链实践（4-PR 审计链 / 5-PR 解耦链）。

**治理** — `maintain/*` + `infra`；拍板；改 flow-plan + git-issue 两 body。

**验证** — 拿一个真实 milestone dry-run，切片各自可独立 review-合且 blocked-by 自洽；不产生层间强耦合切。

### 【P2】3.6 domain-modeling 主动锐化 → flow-intake/flow-plan + doc-author（挂既有工件，不引入 CONTEXT.md）

**落点** — 改 `mj-agent-flow-intake`/`mj-agent-flow-plan`（术语主动锐化纪律）+ `mj-agent-doc-author`（ADR 开列判据）。**不引入 CONTEXT.md**——挂既有 `docs/glossary/upstream_business_warehouse.md` / `biz_catalog/qcm_catalog.yaml` / `decisions/`。

**草案**
- **主动锐化纪律**：intake/plan 中遇术语与既有 glossary/catalog **冲突或模糊** → 当场挑战、用**边界场景压测**（具体 edge case 逼出概念边界）、resolve 后**即时更新**对应工件。
- **ADR 开列判据（借 Matt）**：仅当**难逆 + 反直觉 + 真权衡**三者皆真才开 ADR（写 `decisions/`），与既有 ADR 实践对齐。
- **边界**：跨上游仓术语走 attribution → glossary 元文档 wikilink（跨仓解耦规约）；**catalog 是 4 必停面之一** → 任何 `qcm_catalog.yaml` 改动走 `/mj-agent-runtime-biz-catalog-sync` propose→拍板→apply，不被本纪律绕过。

**集成锚点** — Stage 0/4 + doc-author（Stage 6 ADR 子引擎）；biz-catalog-sync（runtime family，B 风味必停）。

**治理** — `maintain/*` + `infra`；拍板；改 3 个 skill body；catalog 必停不变。

**验证** — 样例术语冲突 dry-run 确认走"挑战→压测→即时更新 glossary"；catalog 改动确认仍被路由到 runtime-biz-catalog-sync 必停（**负向测试**）。

### 落地次序与依赖

**P0(3.1) 先行**——其工艺词汇/checklist（leading words、完成判据、no-op 剪枝）会被 P1/P2 新写的 skill body 复用。**P1(3.2/3.3/3.4)** 补真空缺，三者独立，可并行各起 worktree。**P2(3.5/3.6)** 为原则性增强，依赖 P0 成稿后落更省返工。每项独立 PR、独立拍板。（section 三 末列的 codebase-design 词汇 / 轻量 router / handoff 脱敏 / 架构卫生 ASSESSMENT 仍为 P3 低优先，不在本次 3.1–3.6 实施范围。）

---

## 七、约束与风险

1. **治理张力**：Matt 反框架、轻量；mj-agent 强框架。采纳=把工艺纪律装进治理外壳，**获严谨失自发**（已知代价，非缺陷）。
2. **跨项目借鉴边界**：全程**只借思路**，结构/字段/术语 native 化；**禁止**引入 `CONTEXT.md`、Matt 的 issue 模板/标签、
   setup 安装器等会与 mj-agent native 结构打架的工件。
3. **HITL/权限**：所有 `.claude/**` 与 kernel 文档改动，交互模式逐写拍板（A13/A14 兜底）；必停 4 面（guardrail/precheck/
   prompt/catalog）若被排障/实现触达，仍走原必停，不被新技能绕过。
4. **grilling 校准**：最大失败点是把"前期逼问"误用成"执行门"，违反「方向明确就执行」偏好——SKILL body 必须显式界定。
5. **vault 在 SCAN_ROOTS 外**：草稿不入治理扫描，升格时须手动核验 frontmatter / wikilink 解析。
6. **authoring 方式**：单文档 authoring 用 single-agent + 自验，**不**用 rigid-schema multi-agent workflow（既往两次炸于
   服务端 rate-limit + schema 脆性）。

---

## 八、后续（owner 拍板后）

§六 实施方案 3.1–3.6 / P0–P2 留待 owner 单独拍板后另起 worktree 逐项实现（每项独立 PR、独立拍板）。
升格本草稿：经 `/mj-agent-doc-author` → 顶层 `evidence/assessments/`（vault 在 frontmatter SCAN_ROOTS 外，须手动核验
frontmatter / wikilink 解析）。

---

### 引用（只读调研来源）

- 顶层与分类 README：`mattpocock/skills` `README.md` / `skills/engineering/README.md` / `skills/productivity/README.md`
- 元技能：`skills/productivity/writing-great-skills/SKILL.md`（+ 其 `GLOSSARY.md` 概念）
- 19 个 `SKILL.md`（engineering 14：ask-matt, codebase-design, diagnosing-bugs, domain-modeling, grill-with-docs,
  implement, improve-codebase-architecture, prototype, resolving-merge-conflicts, setup-matt-pocock-skills, tdd,
  to-issues, to-prd, triage；productivity 5：grill-me, grilling, handoff, teach, writing-great-skills）
- 内部映射：mj-agent `.claude/skills/`（34 技能）、`policies/` + `sdd/` kernel、`sdd/workflows/execution-loop.md`、
  ADR-013/016/034 等（并行 Explore 只读勘察）
