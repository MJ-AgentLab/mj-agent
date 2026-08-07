---
type: standard
domain: SKILL
summary: 定义 mj-agent 两类 skill（in-source runtime / in-tree workflow）正文与 description 的写作工艺质量准则——可预测性为根、双负载权衡、信息阶梯、完成判据、leading words、五大失效模式 + no-op 剪枝；是 ADR-013/016 schema 层与 A12 description 最低门之上的「正文质量层」，被 doc-author / runtime-skill-doc-improve / flow-self-review 引用
owner: ranzuozhou
created: 2026-06-22
updated: 2026-08-07
state: draft
version: v1.1
track: shared
tags:
  - standard
  - skill-authoring
  - documentation
aliases:
  - Skill Authoring Craft Standard
  - 技能写作工艺规范
---

# mj-agent 技能写作工艺规范（Skill Authoring Craft）

> **适用范围**：mj-agent **两类** skill 的正文（body）与触发描述（description / activation）的**写作质量**——`src/mj_agent/skills/<name>/SKILL.md`（in-source runtime，Track B）+ `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`（in-tree workflow，Track C）。**不**覆盖 marketplace plugin SKILL（out of governance）。
> **目标受众**：技能作者 / 文档撰写者 / AI Agent
> **版本**：v1.0（draft 首版；从 `[ASSESSMENT]_mattpocock-skills-adoption` §3.1 落地——借「写技能的元哲学」**思路**，按 mj-agent native 规范重新设计，**不** mirror 外部模板）
> **最后更新**：2026-06-22
> **与既有治理的关系**：本规范治「正文 / description **写得好不好**」（质量层）；[[../../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] / [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] 治「**有哪些字段**」（schema 层）；**A12** 治「description **最低门**」（≥200 chars + 反向触发段）；[[../../sdd/adapters/claude-code-skill|claude-code-skill adapter]] / [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] §Standards 治「body section heads + activation 字段 + 5-iteration 循环」。四者**互补不重叠**——本规范是它们之上的正文质量层。

---

## 目录

1. [核心原则·可预测性为根德性](#1-核心原则可预测性为根德性)
2. [双负载权衡（context-load vs cognitive-load）](#2-双负载权衡context-load-vs-cognitive-load)
3. [Description / activation 工艺](#3-description--activation-工艺)
4. [信息阶梯与渐进披露](#4-信息阶梯与渐进披露)
5. [完成判据：checkable + exhaustive](#5-完成判据checkable--exhaustive)
6. [Leading words 词表](#6-leading-words-词表)
7. [五大失效模式 + no-op 测试](#7-五大失效模式--no-op-测试)
8. [与既有治理的边界](#8-与既有治理的边界)
9. [作者自检清单](#9-作者自检清单)
10. [参考](#10-参考)

---

## 1 核心原则·可预测性为根德性

skill 存在的目的，是**从一个随机系统里榨出确定性**。一份好 skill 的成功判据不是"输出文采好"，而是 **agent 每次遇到同类任务都走相同的 process**（相同的步骤、相同的停顿点、相同的留痕）——输出可以因任务而异，**过程必须可预测**。

> **leading word「可预测性」**：本规范下列每一条准则，都是为可预测性服务。当两条准则冲突时，选**更可预测**的那条。

| 可预测性体现在 | 反面（失去可预测性） |
|---|---|
| 每个 Step 有可判定的完成判据 | "产出一份变更列表"——做没做完无法判定 |
| description 触发分支稳定命中 | description 啰嗦/含身份描述 → 漂移触发 |
| body 段落职责单一、不重复 | sediment / duplication → agent 选择性忽略 |

**与 mj-agent 既有文化同源**：可预测性 = `evidence-before-assertion`（先证据后断言）+ HITL 必停拍板（停顿点可预测）+ 17-stage execution-loop（process 固定）在「技能正文」层的投影。

---

## 2 双负载权衡（context-load vs cognitive-load）

两类 skill 的触发机制不同，决定了**剪枝力度**不同：

| 维度 | in-source runtime（Track B） | in-tree workflow（Track C） |
|---|---|---|
| 触发 | `activation` 字段 + `_ACTIVE_SKILLS` 静态全载 → body **常驻 LLM context** | Claude Code 主 process auto-discover；description **常驻 context**，body 命中才加载 |
| 主要负载 | **context-load**（body 每个字都进 system prompt，吃 token 预算） | **context-load**（description 每个字常驻）+ body 命中后的 cognitive-load |
| 剪枝准则 | body 越短越好；深度内容下推到 `references/`（渐进披露，见 §4） | **description 比 body 更须狠剪**——它无条件常驻；body 可适度展开 |

**核心权衡**：每多写一句，要么增加 context-load（常驻成本），要么增加 cognitive-load（agent 读它的认知成本）。**默认假设"少即是多"**——除非一句话能改变 agent 的默认行为（见 §7 no-op 测试），否则它是纯负载。

> ❌ Anti-pattern：把"背景介绍 / 设计动机 / 历史沿革"塞进 body 顶部。这些是 cognitive-load 而非行为指令；该进 `references/` 或 ADR，不进 body。

---

## 3 Description / activation 工艺

> 本节是 **A12 最低门之上的质量层**。A12 管"≥200 chars + 含 `Do not use for:` 反向触发段"（[[../../sdd/adapters/claude-code-skill|claude-code-skill]] §Standards / §CI Gate）；本节管"这 200+ 字**写得好不好**"。

**3.1 前置 leading word**——description 首句用一个紧凑概念锚定身份（"This skill runs mj-agent disciplined bug diagnosis …"），让 routing 第一眼判定领域。

**3.2 一触发分支一句**——每个"用户说 X / 在 Y 场景"对应一个独立 trigger 子句。**同义改写 = duplication（§7）必须合并**：`"排查 bug" / "debug this" / "为什么失败"` 是同一分支的多语言别名，列在一句里，不拆三句。

**3.3 删身体已有的身份**——description 不重述 body 已说清的"我是谁、我做什么细节"。description 只留两类内容：
- **触发词**（正向：何时调用）；
- **reach 子句**（反向 + 边界："另一个 skill 才是对的时候用那个"——即 `Do not use for:` 段）。

**3.4 undertriggering 是默认失败模式**（in-source `activation` 尤甚，per [[../../sdd/adapters/runtime-skill|runtime-skill]] §Standards）——初版描述通常偏保守 → 该触发没触发（沉默失败，无报错）。优化方向通常是**放宽 + 补正向关键词**，经 ≤5 轮 iteration 收敛，而非收紧。

---

## 4 信息阶梯与渐进披露

把内容按"agent 何时需要"分三级，**只把每一步真正要用的放进当前层**：

```text
in-skill step       —— 有序动作（agent 每次都走）          → 进 body 主线
in-skill reference  —— 按需查的规则 / 表 / 边界            → 进 body 末尾 reference 段 或 ## Reference Files
external reference   —— 深度资料 / 长 schema / data dict     → 经 context pointer 推到独立文件，命中才加载
```

- **in-source（Track B）**：external reference 用 `references/` 子目录承载（渐进披露治理见 [[../../sdd/adapters/runtime-skill|runtime-skill]] §Standards「渐进披露」+ [[../../decisions/ADR-003_Progressive_Disclosure|ADR-003]]）；`scripts/` / `assets/` 同理**不随 body 入 context**。
- **in-tree（Track C）**：深度内容推到 kernel 文档（`sdd/` / `policies/`）或 `docs/`，body 用 `[[wikilink]]` / 路径做 context pointer 引用，**不复制正文**。

> **判据**：只被**部分** branch 用到的内容，必须下推一层。若一段内容 agent "大多数时候不读"，它不该在当前层。

---

## 5 完成判据：checkable + exhaustive

每个 Step **以一条可判定 done / not-done 的判据结尾**。这是防 **premature completion（抢跑，§7）** 的主闸。

| ✅ checkable + exhaustive | ❌ 模糊（抢跑温床） |
|---|---|
| "每个改动文件的 track 都已登记" | "产出一个变更列表" |
| "ruff / mypy / pytest 三者均 PASS（贴输出）" | "本地验证通过" |
| "design-tree 每个分支标 resolved 或 defer(M-FU)" | "需求已澄清" |

**判据要 exhaustive**：能穷举的就穷举（"三者均 PASS"而非"测试通过"）。

**何时 sequence-split**：仅当**判据 irreducibly 模糊**且**观察到 agent 抢跑**时，才把后续步骤拆成隐藏的下一 Step（让 agent 必须显式推进）。不要预防性地过度拆分——那增加 cognitive-load。

---

## 6 Leading words 词表

leading word = 用一个**预训练里已有的紧凑概念**锚定一类行为，复用而非每次重述。mj-agent 已沉淀以下 leading words，**新 skill 应复用**：

| Leading word | 锚定的行为 | 出处 |
|---|---|---|
| **必停** | 遇此面暂停、等 Owner 拍板，不单方翻转 | CLAUDE.md 必停 surfaces / [[../../policies/ai-agent|ai-agent]] |
| **拍板** | AI 提议 → Owner 决策 → AI 落盘 | [[../../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]] |
| **风味（A/B/C）** | 改动归属代码 / agent / 工程编排三轨 | tri-track 治理 |
| **Level（A/B/C）** | 验证矩阵分级（ruff/mypy/pytest …） | [[../../sdd/workflows/execution-loop|execution-loop]] §5 |
| **红信号** | 会对"这个 bug"变红的 tight deterministic 反馈环 | flow-diagnose（P1 规划中） |
| **纵切 / tracer-bullet** | 端到端穿透各层的窄而完整切片 | flow-plan（P2 规划中） |
| **逼问** | 前期对真歧义一次一问 + 推荐答案锚点（≠执行门） | flow-intake/plan（P1 规划中） |

> 写新 skill 时遇到上表已覆盖的行为，**直接引用 leading word + 一句话**，不重述其完整定义（重述 = duplication）。

---

## 7 五大失效模式 + no-op 测试

| # | 失效模式 | 症状 | 修法 |
|---|---|---|---|
| 1 | **premature completion（抢跑）** | agent 提前宣布"done"，跳过后续步骤 | Step 加 checkable + exhaustive 判据（§5）；必要时 sequence-split |
| 2 | **duplication（重复）** | 同一规则/触发词在多处同义改写 | 合并到单一真相源；description 一分支一句；body 引用 leading word |
| 3 | **sediment（沉积）** | 历史增补层层堆积，旧指令与新指令并存矛盾 | 改 skill 时**删旧立新**，不只追加；矛盾段就地清除 |
| 4 | **sprawl（蔓延）** | body 越写越长，混入背景/动机/历史 | 渐进披露下推（§4）；背景进 ADR/reference |
| 5 | **no-op（空转）** | 一句话删掉后 agent 行为不变 | **no-op 测试**（见下） |

> **no-op 测试（每句必过）**：把这句删掉，agent 的默认行为会改变吗？
> - **不会改变** → 这句是纯负载（context-load / cognitive-load），**删整句**。
> - **会改变** → 保留。
>
> no-op 测试是 §1 可预测性、§2 双负载、§4 渐进披露在「单句粒度」上的统一执行手段——写完一段，逐句过一遍。

---

## 8 与既有治理的边界

本规范**只治正文质量**，与以下治理**互补不重叠**，不得越界重述其规则：

| 治理 | 管什么 | 真相源 |
|---|---|---|
| 本 STANDARD | 正文 / description **写得好不好**（质量层） | 本文件 |
| ADR-013 / ADR-016 | skill **有哪些字段**（2-field schema / namespace） | [[../../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] / [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] |
| A12 | description **最低门**（≥200 chars + 反向触发段） | [[../../sdd/adapters/claude-code-skill|claude-code-skill]] §Standards / §CI Gate |
| runtime-skill §Standards | in-source body **section heads（6 段）** + `activation` + 5-iteration 循环 | [[../../sdd/adapters/runtime-skill|runtime-skill]] |
| claude-code-skill §Standards | in-tree body 必含 `## Overview` + `## Workflow` + family enum | [[../../sdd/adapters/claude-code-skill|claude-code-skill]] |

> **必停不可绕**：任何 skill 正文修改若触达 4 必停面（`tools/sql/guardrail.py` / `precheck.py` / `prompts/system.md` / `skills/*/SKILL.md` body / `qcm_catalog.yaml`），仍走 [[../../policies/ai-agent|ai-agent]] §8/§9 propose→拍板→apply，本规范不提供绕过通道。in-source SKILL body 改动属 B 风味必停（`runtime-skill-content-change`）。

---

## 9 作者自检清单

写完 / 改完一份 skill，逐项过（被 [[../../sdd/workflows/execution-loop|execution-loop]] Stage 11 self-review + doc-author / runtime-skill-doc-improve 引用）：

- [ ] **可预测性**：同类任务下 process 固定？每个 Step 有可判定完成判据（§5）？
- [ ] **双负载**：body / description 是否已按 §2 剪枝？in-source body 是否够短？
- [ ] **description**：前置 leading word？一触发分支一句、无同义 duplication？删了 body 已有的身份？含 `Do not use for:` 反向段（A12）？≥200 chars（A12）？
- [ ] **渐进披露**：只被部分 branch 用到的内容已下推到 reference / `references/` / kernel doc（§4）？
- [ ] **leading words**：复用了 §6 词表，未重述其定义？
- [ ] **no-op 测试**：逐句过——每句删掉都会改变默认行为？纯负载句已删（§7）？
- [ ] **失效模式**：无 premature completion / duplication / sediment / sprawl / no-op（§7）？
- [ ] **边界**：未越界重述 ADR-013/016 / A12 / adapter §Standards 的规则（§8）？触达必停面的改动走 propose→拍板→apply？

---

## 10 参考

- [[../../evidence/assessments/[ASSESSMENT]_mattpocock-skills-adoption|mattpocock-skills 采纳评估]] §3.1（本规范的思路来源 + 借鉴边界；2026-06-22 已升格入仓 `evidence/assessments/`）
- [[../../sdd/adapters/claude-code-skill|sdd/adapters/claude-code-skill]] §Standards / §CI Gate（A12；in-tree 2-field schema）
- [[../../sdd/adapters/runtime-skill|sdd/adapters/runtime-skill]] §Standards（in-source 13-field；`activation` + 5-iteration + 渐进披露）
- [[../../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs marketplace schema 分离）
- [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（`mj-agent-<group>-<verb>` namespace + 5 family + lifecycle）
- [[../../decisions/ADR-003_Progressive_Disclosure|ADR-003]]（渐进披露原则）
- [[../../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]（拍板模型；必停不可绕）
- [[../../sdd/workflows/execution-loop|sdd/workflows/execution-loop]] §5 Level 矩阵 + §6 AI Self-review 检查清单
- [[STANDARD]_GitHub_Markdown|GitHub-Flavored Markdown 编写规范]]（本文件遵循的 GFM 语法基线）
