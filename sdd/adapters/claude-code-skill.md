---
type: sdd-adapter
artifact: claude-code-skill
state: draft
version: 0.5
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-01
track: engineering-workflow
ai_visibility: source-of-truth
---

# Adapter: Claude Code Skill (in-tree workflow)

> Phase M2 内容化 — Claude Code Skill adapter 治理 `.claude/skills/mj-agent-*/` in-tree
> workflow SKILL 的 ADR-013 native schema + ADR-016 namespace 契约.
> §Standards / §BDD Rules / §TDD Rules 各段顶部 cross-ref 蓝图 `spec-anchored-calm-lampson.md`
> 手册 §22.7 Claude Code Skill Adapter Standards.

## §Scope

**Included** — Claude Code Skill adapter 治理：

- `.claude/skills/mj-agent-<group>-<verb>/SKILL.md` — per ADR-016 namespace pattern
- 5 families（flow / git / doc / runtime / infra）；实测 SKILL 计数以
  `scripts/sdd/check_claude_skill_contracts.py --all` 为准（现 on-disk 37；evidence family
  4 SKILL 属 Phase-2 规划未落地）
- Claude Code 主 process 加载（不入 `mj_agent` Python runtime；不走 `load_skill`）
- ADR-013 2-field native schema（`name` + `description` 仅 2 字段；**不**用 13-field
  Agent_Side schema）

**Excluded** — 其他 adapter 治理：

- `src/mj_agent/skills/*/SKILL.md` — in-source canonical（→ `runtime-skill` adapter；同时也受
  `prompt` adapter schema 治理）
- Marketplace plugin SKILL（`mj-agentlab-marketplace/plugins/*/`）— out of mj-agent
  governance；plugin 自身有 governance 边界
- `.claude/scripts/**/*.ps1` — Claude Code workflow scripts；非 SKILL；不在本 adapter scope
- `.claude/hooks/**/*` — hooks；非 SKILL；不在本 adapter scope

**Adapter 三源 SKILL 边界对照** (per CLAUDE.md §"Three-source SKILL distinction")：

| 源 | 路径 | Schema | Loader | 本 adapter |
|---|---|---|---|---|
| in-source (runtime) | `src/mj_agent/skills/<name>/` | 13-field (Agent_Side §2) | `load_skill()` strip | NOT 本 adapter（runtime-skill） |
| in-tree (workflow) | `.claude/skills/mj-agent-*/` | 2-field (ADR-013 native) | Claude Code 主 process | **本 adapter** |
| marketplace plugin | `mj-agentlab-marketplace/plugins/<plugin>/` | 2-field (ADR-013 native) | Claude Code plugin loader | out of mj-agent governance |

### `.claude/` 新目录准入规则

> 源：Meta_Framework STANDARD §3.6 新目录准入规则（engineering-workflow 专属条目）+
> §7.6 `.claude/` 边界。决策依据
> [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（in-tree
> `mj-agent-*` namespace + lifecycle）+
> [[../../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs
> marketplace schema 分离）。本规则界定哪些 `.claude/` 新目录可由普通 PR 直接引入、哪些需
> kernel-policy 修订。

| 新目录 / 资源 | 准入门槛 | 说明 |
|---|---|---|
| `.claude/skills/mj-agent-<group>-<verb>/`（**既有 5 family 内**的新 skill） | **普通 PR 直接新增** —— 无需 Meta / kernel 修订 | 仅需符合 ADR-016 `mj-agent-<group>-<verb>` namespace + 通过 A12 description 质量门；不触动 kernel-policy。`flow` 由 9 增至 10 即走此路径（ADR-016 `:74` 补记明写「在 5 family namespace 内，**未**触发新 family → ADR 修订条件」） |
| **新增第 6 个 family** | **需另开 ADR** —— 非普通 PR | `decisions/ADR-016` 决策点 1 定 `<group>` ∈ {flow, git, doc, runtime, infra} 为「5 个固定 family，不允许扩展（除非另开 ADR）」，其 `:179` 亦以未来的 `eval` family 为例说明那会「触发 ADR 修订」。实现站 ADR-016 一侧：`scripts/sdd/check_claude_skill_contracts.py` 把该 5 值枚举硬编码进 `_ADR_016_NAMESPACE_PATTERN`，第 6 family 的 skill 必产 namespace-mismatch finding。⚠ 该 finding 是 `Severity.WARN` 且 CI 调用不带 `--strict`，故它**不阻断合并** —— 真正的门是本行这条 ADR 要求，执行体只是佐证（口径差异见 issue #496） |
| `.claude/hooks/`（**首次启用**） | **需 kernel-policy 修订** —— Meta §7.6 `.claude/` 边界子条款 | hooks 影响所有工具调用，治理强度高；首次引入 hooks 必须先修订 §7.6.x 子条款（kernel-policy 级），再落 hooks 文件；不可由普通 PR 直接引入 |
| `.mcp.json` server 增删 | **联动 MCP_Server_Governance STANDARD（A14）** | 详见下方注；本 adapter 不重复 |

**`.mcp.json` 半边由别处覆盖**：`.mcp.json` server 增删的准入 / trust posture / credential
mode 已由 `policies/ai-agent.md` §4 `mcp-server-trust-posture-change`（A14 必停 gate）+ 领域
专属 `capabilities/infrastructure/mcp-server-governance/`（capability；former MCP STANDARD archived M6 X5）覆盖；本 adapter
只承载 **skills / hooks 两半** 的显式准入规则，`.mcp.json` 半不在此重述。

**Cross-ref**：`.claude/settings.json` 的 A13 PR 阻塞条件（裸 `Bash` 禁用 / `permissions.deny`
secret pattern 兜底 / `enabledPlugins` justification）见 `policies/ci-gates.md` §5.1。三者
（settings.json A13 / skills+hooks 准入 / `.mcp.json` A14）共同构成 engineering-workflow track
的 `.claude/` 边界 PR 门禁面。

## §Contract Output

`<capability>/contracts/claude-skill.contract.yml` — per capability one file，描述本 capability
治理的 in-tree workflow SKILL 集合（schema 见 `sdd/templates/contracts/claude-skill.contract.
yml.template`）.

M2 Stage C 新增 1 contract：

- `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml` —
  指向 `.claude/skills/mj-agent-infra-*` family。per-SKILL 记 `name` + `file` + `frozen_at` +
  **三个 freeze 摘要**：`description_hash`（frontmatter `description` 字符串的 sha256）、
  `body_content_hash`（canonical regex-strip 后的 body）、`body_section_heads`。
  ⚠ 记的是**摘要不是字段实际值** —— 原文写「`name` + `description` 字段实际值」不实（#497 ①）。

## §Standards

> 本节对应蓝图手册 §22.7 Claude Code Skill Adapter Standards.

### §Standards.1a 技能正文工艺质量（指针）

> **A12**（§CI Gate）只管 description **最低门**（≥200 chars + `Do not use for:` 反向触发段）；description / body **写得好不好**（可预测性为根、双负载权衡、信息阶梯、leading words、no-op 剪枝、五大失效模式）由 [[../../docs/rule/[STANDARD]_MJ_Agent_Skill_Authoring_Craft|技能写作工艺规范]]（正文质量层，单一真相源；本 adapter **不复制其正文**）治理。in-tree workflow SKILL 起草 / 改写应过其 §9 作者自检清单。

**Required fields** (contract YAML schema)：

- `skill_path` — `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`
- `namespace_pattern: "mj-agent-<group>-<verb>"` — ADR-016 namespace 校验
- `schema: ADR-013-native` — 固定值；标识 2-field schema（区别 13-field 不同 adapter 治理）
- `description_requirements`：
  - `min_chars: 200`
  - `must_contain_reverse_trigger: "Do not use for:"`（反向 trigger block 必有）
- `sections_required[]` — body 必含 `## Overview` + `## Workflow`（其他 sections 如
  `## Anti-patterns` / `## Handoff` 灵活，不强制）
- `family` — 5 family 之一（`flow` / `git` / `doc` / `runtime` / `infra`）per ADR-016
- `owner_approval_required: bool` — `runtime` family 必须 `true`（mj-agent-runtime-* skill
  落盘前必须过工具中立 `OWNER_APPROVAL_REQUIRED` 停点，ADR-034 propose→拍板→apply；未经拍板
  不写 `src/mj_agent/{skills,prompts,agent.py,tools}/`）

**Per-SKILL freeze 字段**（M2 新 contract 用）：

```yaml
skills:
  - name: mj-agent-infra-llm-endpoint-probe
    file: .claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md
    description_hash: sha256:...          # frontmatter `description` 字符串的 sha256
    body_content_hash: sha256:...         # canonical regex-strip 后的 body
    frozen_at: 2026-05-21T...Z
    body_section_heads: ["## Overview", "## Workflow", ...]
  - name: mj-agent-infra-env-teardown
    file: .claude/skills/mj-agent-infra-env-teardown/SKILL.md
    description_hash: sha256:...
    body_content_hash: sha256:...
    frozen_at: 2026-05-21T...Z
```

**Optional fields**（M3+ 落地）：

- `stage_mapping` — 与 HITL_Prompt 17 stage 对齐
- `hitl_triggers[]` — SKILL 内部 HITL 触发条件清单（非必停 surface；advisory）

**`hitl_required[]`** — 仅 gate ID 引用（hyphen canonical per C5）：

```yaml
hitl_required:
  - mcp-server-trust-posture-change      # MCP server 信任边界变更（M3+ 起命名）
```

注：claude-code-skill 触达的必停 gate 与 4 项专属必停（sql-guardrail-relax /
prompt-version-bump / biz-catalog-sync / runtime-skill-content-change）不重叠；本 adapter 关
联的 gate 在 M3+ 命名落地（A12-A14 PR gate；MCP server governance 维度）.

## §Current mj-agent Implementation Status

> **新节** — 不沉默 baseline deviation（per Q-A3）.

**当前状态：零 schema deviation，决议已收口。** 本节**刻意不写死计数**，判据是可复跑命令：

```bash
uv run --frozen --no-sync python scripts/sdd/check_claude_skill_contracts.py --all | tail -2
# 2026-09-01 实测 → PASS skills: 37 / WARN findings: 0 / FAIL: 0
```

**⚠ M2 期记的「34/34 SKILL 全员 markdown-body-only convention」从来不是实况，而是一条 spurious
validator 输出** —— 后续单元不得把它当历史事实转述。根因 = V4 执行体的 `yaml.safe_load()` 把
`description` 里字面 `"Do not use for: "` 的 `": "` 当成嵌套映射起始而抛 `YAMLError`，于是每个
SKILL 都被误报「no frontmatter block」（调查登记 `03f1bc7`、修复 `a5614c4`，均 2026-05-21；
`policies/ai-agent.md` §7 Subsection A 第 1 条把它记作「V4 false-claim intercept」）。
`.claude/skills/` 的 SKILL **自首个提交起就带 ADR-013 2-field frontmatter**（判据
`git show 97361dd:.claude/skills/mj-agent-git-branch/SKILL.md | head -3`），仓内**从未**发生过
frontmatter backfill migration。

**Resolution — 已闭合，不再是待决项**：`M3-FU-CLAUDE-SKILL-ADR` 因前提被证伪而**改判范围**
（`f6290cc`），产出 `decisions/ADR-032_Claude_Skill_Schema_Monitoring.md`（`state: active` /
`decision: accepted`；2026-07-23 #372 由 draft promote），目标由「修既存 deviation」改为
「防未来 deviation」的 **3 层监控 regime**：Layer 1 = 本 adapter §CI Gate 的 V4 执行体、
Layer 2 = A12 PR 模板自检、Layer 3 = A6 季度审计。

⇒ 原 **Option A**（给执行体加 `--advisory-mode` flag）与 **Option B**（一次性 backfill
migration）**均未执行、亦不再待决**。`--advisory-mode` 至今不存在于执行体（判据
`grep -c advisory scripts/sdd/check_claude_skill_contracts.py` → 0）。

**contract 侧**：`capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`
冻结 8 个 `mj-agent-infra-*` SKILL，其 `description_hash` 取的是 **frontmatter `description`
字段字符串**的 sha256 —— **不是** body 首行 proxy。

## §BDD Rules

> 本节对应蓝图手册 §22.7 BDD Rules（Claude Code SKILL trigger fidelity tagging）.

**`@adapter:claude-code-skill` 何时用** — SKILL trigger fidelity scenario：

- SKILL `description` 正向 trigger 判定（"用户说 X 时 SKILL 应被调用"）
- SKILL `description` 反向 trigger 判定（"`Do not use for:` 内场景不应被调用"）
- SKILL 在错误 stage 被调用（防 stage mapping drift）

**`@adapter:claude-code-skill` 何时 NOT 用** — 防 scenario 爆炸：

- ADR-013 schema validation（`name` 是否 match directory；description ≥ 200 chars）→ 用
  script gate 直接校验，不入 BDD
- SKILL body 排版 / typo → 不加 `@adapter` tag；走人工 review
- `.claude/scripts/*.ps1` 行为 → 非 SKILL adapter 范围

**`@risk:high` SKILL** — 必有 BDD 配套：

- `mj-agent-git-commit` / `mj-agent-git-push` — 写 git 状态；误触发风险高
- `mj-agent-infra-env-teardown` — destructive infra 操作；3-level safety 必 BDD 覆盖
- `mj-agent-runtime-*` family 4 SKILL — 拍板前 propose-only（`owner_approval_required`），但若
  BDD 不覆盖可能漂移成"sneak write"（未经拍板直写）

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:claude-code-skill @risk:high
Scenario: mj-agent-git-push refuses to run on protected branches
  Given current branch is "main"
  When user invokes /mj-agent-git-push
  Then the skill refuses with a "Do not use for:" reverse trigger match
  And no git push command is executed
```

## §TDD Rules

> 本节对应蓝图手册 §22.7 TDD Rules（claude-skill schema-layer test-first + 反向 promote）.

**Contract-test-first 限于 schema layer**：

- `claude-skill.contract.yml` 的 `skills[].name` / `namespace_pattern` / `family` /
  `owner_approval_required` 字段变更 → 必先有 failing test（M3 起）
- SKILL `description` ≥ 200 chars + 含 `Do not use for:` block → script 自动校验
- Trigger fidelity（`description` 是否真能让 Claude 在正确时机调用）走 **manual HITL** —
  script 看不出意图

**`_common.frontmatter` 接口在本 adapter 的特殊处理**：

- V4 执行体 `Path.read_text` 之后走 `scripts.sdd._common.parse_native_frontmatter` 读 ADR-013
  2-field frontmatter，**没有 markdown-body-only fallback 路径**；`name` 取自 frontmatter，
  目录名只作**一致性交叉校验**（`name != dirname` 判 WARN），不是 `name` 的来源。
  ⚠ 原记的「走正则 fallback 从 dir 推 `name` / 从 body 首段推 `description`」是 M2 期基于那条
  spurious validator 输出写下的，实现从未如此 —— 判据
  `sed -n '60,95p' scripts/sdd/check_claude_skill_contracts.py`。
- 与 `runtime-skill` adapter 形成对比：runtime SKILL 走 `load_skill` **strip** 13-field
  frontmatter 后把 body 拼进 system prompt；Claude Code SKILL 的 2-field frontmatter 由
  Claude Code 主 process 自身消费，不入 `mj_agent` Python runtime。

**Red-Green-Refactor 软模式 RD10=C** — 同其他 adapter；AI-generated SKILL 允许 "test
alongside SKILL.md"（同一 PR 内含 test + 实装；不强制先 commit failing test）；人工编写仍走
严格 red-green.

**G28 联动** — `claude-skill.contract.yml` `skills[]` 增删 / `frozen_at` 重签 → 必须配套
`tests/contracts/<capability>/test_claude_skill_contract.py` 内 failing→green 转变.

**反向 promote 候选** — 已失效（前提不成立）：原候选是把「markdown-body-only 提取逻辑
（dir → name；body 首段 → description）」promote 到 `_common`，但该逻辑从未存在（见上一条与
§Current mj-agent Implementation Status）。真实共享面是既有的
`scripts.sdd._common.parse_native_frontmatter`，**已在 `_common` 内**，无需 promote.

## §CI Gate

**Script gate**: `scripts/sdd/check_claude_skill_contracts.py`

- **Phase**: 首发 M2 warning，现 **blocking**（`sdd/gates.md` `:56` 的 `V4 Claude-Skill` 行记
  `blocking@ci`）。⚠ 原文引「per `sdd/gates.md` G3 切换节奏」是**误引** —— `G3` 是
  `check_contracts.py`（`:33`，至今 `warning@ci`），与本 gate 无关。⚠ **姿态载体与
  行为真值须分开读**：`ci.yml` 的 V4 step 名与 `sdd/gates.md` 的 V4 行都记 `BLOCKING`、该 step
  亦无 `continue-on-error`，但执行体的 finding 全为 `Severity.WARN` 而 CI 调用不带 `--strict`，
  故 `Summary.exit_code(strict=False)` 恒 0。该口径差异登记在 **issue #496**，本 adapter 不代为
  判定（`policies/ci-gates.md` §1.1「姿态载体有四种」的一个实例）
- **Triggers**: `capabilities/*/contracts/claude-skill.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（namespace mismatch / `description` <200
  chars / 缺失 reverse trigger block / family 不在 5 enum）
- **Implementation**: `skills_dir.glob("*/SKILL.md")` 扫描—— 注意是 **全部** skill 目录而非
  `mj-agent-*` 前缀子集（`name` 不合 ADR-016 namespace 正是它要报的 finding 之一，先限定
  前缀就自我屏蔽了）；继而 `parse_native_frontmatter` 读 2-field frontmatter。
  ⚠ 原记的「`Path.glob('.claude/skills/mj-agent-*')`」与「正则提取 description」**两项均不实**，
  判据 `grep -n "glob" scripts/sdd/check_claude_skill_contracts.py`。

**Baseline noise** — 已归零；原「预期 ~34 WARN」记载作废（它建立在上文被证伪的
markdown-body-only 前提上）。当期真值以执行体输出为准，本节**刻意不写死数字**：

```bash
uv run --frozen --no-sync python scripts/sdd/check_claude_skill_contracts.py --all | tail -2
# 2026-09-01 实测 → PASS skills: 37 / WARN findings: 0 / FAIL: 0
```

- 出现非零 WARN 即是**真实 finding**，不再有「expected noise」豁免口径，reviewer 应按 A12 处理。
- 持续合规由 `decisions/ADR-032_Claude_Skill_Schema_Monitoring.md` 的 3 层 regime 承担
  （Layer 1 本 gate / Layer 2 A12 PR 模板 / Layer 3 A6 季度审计）。

**M2 → M3 切换条件**：

- Stage C 1 新 contract（`mcp-server-governance/claude-skill.contract.yml`）schema layer PASS
  —— **已满足**
- ~~`_common` markdown-body-only 提取接口稳定（如 promote 落地）~~ —— **作废**：该接口从未存在，
  实际共享面是 `_common.parse_native_frontmatter`（见 §TDD Rules 反向 promote 候选条）
- `M3-FU-CLAUDE-SKILL-ADR` 决议产出（option A / B 任一）—— **已满足，但结论是第三条路**：
  两 option 均未采纳，改判为 `decisions/ADR-032_Claude_Skill_Schema_Monitoring.md` 的
  drift-prevention regime

---

> *Phase M2 content — `state: draft`.*
>
> *v0.5（2026-09-01）：#497 ① + ② —— §Current mj-agent Implementation Status / §TDD Rules /
> §CI Gate 三节停在 2026-05 的 M2 记载真值化。核心更正：「34/34 markdown-body-only convention」
> **从来不是实况**，而是 V4 执行体 `yaml.safe_load()` 被 `"Do not use for: "` 里的 `": "` 骗出的
> spurious 输出（`03f1bc7` 调查 / `a5614c4` 修复），故 Option A / Option B **都没执行、也不再待决**
> —— `M3-FU-CLAUDE-SKILL-ADR` 已改判范围（`f6290cc`）并产出 `ADR-032`（active / accepted，#372）。
> ⚠ 这条更正推翻了 issue #497 正文对本项的归因（原写「Option B 其实早已落地」）。同批清掉同一
> 前提在本文件的**另外五处**渗漏（issue 只点名两处，实测更广）：§TDD Rules loader 接口段的
> 「正则 fallback 从 dir 推 name」、§TDD Rules 反向 promote 候选、§CI Gate 的 M2→M3 切换条件第 2 条、
> §CI Gate `Implementation` 行的 glob 与「正则提取 description」（实为 `glob("*/SKILL.md")` +
> `parse_native_frontmatter`）、§Standards YAML 示例里的 `description_first_line`（全仓仅本文件出现，
> 真实契约字段是 `description_hash` + `body_content_hash` + `body_section_heads`）。另修 §CI Gate
> `Phase` 行的**误引** —— 原引 `sdd/gates.md` 的 `G3`，而 G3 是 `check_contracts.py`（`:33`，仍
> `warning@ci`），本 gate 是 `:56` 的 `V4 Claude-Skill` 行（`blocking@ci`）。计数一律改为可复跑推导
> 而非写死数。**`:25-26` 的「现 on-disk 37」有意不动**（活值且当前为真，已用 SoT 指针体裁）。
> §Scope 准入表拆成两行以消解与 `ADR-016` 决策点 1 的直接矛盾：既有 5 family 内新增 skill 走普通
> PR，**新增第 6 family 须另开 ADR**。**零执行体改动、零 gate 姿态 delta**；V4「记 BLOCKING 但恒
> exit 0」的口径差异只作指针登记到 issue #496，本文件不代为判定。*
