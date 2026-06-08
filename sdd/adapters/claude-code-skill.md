---
type: sdd-adapter
artifact: claude-code-skill
state: draft
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-04
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
- 5 families 当前实测 ~34 SKILL（flow / git / doc / runtime / infra；Phase M6 新增 evidence
  family 4 SKILL → 36 终态）
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
| `.claude/skills/<group>/`（新 skill family 目录） | **普通 PR 直接新增** —— 无需 Meta / kernel 修订 | 仅需符合 ADR-016 `mj-agent-<group>-<verb>` namespace + 通过 A12 description 质量门；不触动 kernel-policy。5 family（flow / git / doc / runtime / infra）已立，新增第 6 family（如 M6 evidence）走此路径 |
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
  指向 `.claude/skills/mj-agent-infra-*` family（per-SKILL 描述 `name` + `description` 字段
  实际值 + `frozen_at`）.

## §Standards

> 本节对应蓝图手册 §22.7 Claude Code Skill Adapter Standards.

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
- `read_only_by_design: bool` — `runtime` family 必须 `true`（mj-agent-runtime-* skill 不修改
  `src/mj_agent/{skills,prompts,agent.py,tools}/`）

**Per-SKILL freeze 字段**（M2 新 contract 用）：

```yaml
skills:
  - name: mj-agent-infra-llm-endpoint-probe
    file: .claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md
    description_first_line: "Probe LLM endpoint health by ..."
    frozen_at: 2026-05-21T...Z
  - name: mj-agent-infra-env-teardown
    file: .claude/skills/mj-agent-infra-env-teardown/SKILL.md
    description_first_line: "Teardown mj-agent env with 3-level safety ..."
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

**M2 实测观察**（V4 在 Stage A 末跑 `check_claude_skill_contracts.py` against 全 34 SKILL）：

- 34/34 SKILL **全员 "markdown-body-only convention"** — body 富文本无 YAML frontmatter
- 与 ADR-013 2-field schema **ideal** 形成 **baseline deviation**：ADR-013 定义 `name` +
  `description` 是 frontmatter 字段；当前实装 `name` 由 directory name 推断、`description`
  由 body 首段或 first heading 后段落推断

**Resolution path** — 两 option，待 M3-FU ADR 决议：

- **Option A — accept markdown-body-only as advisory**：保留当前 convention；ADR-013 schema
  字段降级为 "ideal reference"；`check_claude_skill_contracts.py` 加 `--advisory-mode` flag；
  baseline noise 可控
- **Option B — Phase M5 backfill frontmatter**：跑一次性 migration 把 ADR-013 2-field 字段
  backfill 到全 34 SKILL frontmatter；后续 schema 严格；M5+ 0 baseline noise

**Cross-ref**：`plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown 条目
`M3-FU-CLAUDE-SKILL-ADR`（独立小 PR；M3 startup 后立项；resolution 决议产出独立 ADR）.

**M2 期 contract 描述 current state** — 本 adapter 的 M2 新 contract（`mcp-server-governance/
claude-skill.contract.yml`）描述当前 markdown-body-only convention（`description_first_line`
作 freeze proxy 而非 frontmatter `description` 字段）；不要求 backfill；ADR 决议后回填本节
resolution status + 必要时 contract refactor.

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
- `mj-agent-runtime-*` family 4 SKILL — read-only by design，但若 BDD 不覆盖可能漂移成"sneak
  write"

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
  `read_only_by_design` 字段变更 → 必先有 failing test（M3 起）
- SKILL `description` ≥ 200 chars + 含 `Do not use for:` block → script 自动校验
- Trigger fidelity（`description` 是否真能让 Claude 在正确时机调用）走 **manual HITL** —
  script 看不出意图

**`_common.frontmatter` 接口在本 adapter 的特殊处理**：

- markdown-body-only SKILL **不**调用 `load_frontmatter`（无 frontmatter 可加载）；走 plain
  `Path.read_text` + 正则 fallback 提取 `name`（from dir）+ `description`（from body 首段或
  `## Overview` 段）
- 与 `runtime-skill` adapter 形成对比：runtime SKILL 必须走 `load_skill` strip frontmatter；
  Claude Code SKILL 反之

**Red-Green-Refactor 软模式 RD10=C** — 同其他 adapter；AI-generated SKILL 允许 "test
alongside SKILL.md"（同一 PR 内含 test + 实装；不强制先 commit failing test）；人工编写仍走
严格 red-green.

**G28 联动** — `claude-skill.contract.yml` `skills[]` 增删 / `frozen_at` 重签 → 必须配套
`tests/contracts/<capability>/test_claude_skill_contract.py` 内 failing→green 转变.

**反向 promote 候选** — M3+ 视需求把 markdown-body-only 提取逻辑（dir → name；body
首段 → description）promote 到 `_common.discovery` 或新建 `_common.claude_skill_parse`.

## §CI Gate

**Script gate**: `scripts/sdd/check_claude_skill_contracts.py`

- **Phase**: M2 warning / **M3 blocking**（per `sdd/gates.md` G3 切换节奏；但见下方 baseline
  noise 说明）
- **Triggers**: `capabilities/*/contracts/claude-skill.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（namespace mismatch / `description` <200
  chars / 缺失 reverse trigger block / family 不在 5 enum）
- **Implementation**: `Path.glob('.claude/skills/mj-agent-*')` 扫描 + 正则提取 description +
  cross-check contract `skills[]` 列表

**Baseline noise** — **预期 ~34 WARN**（markdown-body-only deviation；ADR-013 2-field schema
不命中 frontmatter 字段）：

- M2 末 CI toggle PR-M2-3 description **必须显式说明此 noise 是 expected**，per
  `M3-FU-CLAUDE-SKILL-ADR` 待决；不算 false-positive，reviewer 不应阻 PR
- M3+ ADR 决议后调整：
  - 若 option A → 加 `--advisory-mode` flag；advisory mode 下 markdown-body-only 视为 PASS；
    期望 0 WARN
  - 若 option B → 跑一次性 backfill migration（独立 PR）；之后期望 0 WARN

**M2 → M3 切换条件**：

- Stage C 1 新 contract（`mcp-server-governance/claude-skill.contract.yml`）schema layer PASS
- `_common` markdown-body-only 提取接口稳定（如 promote 落地）
- `M3-FU-CLAUDE-SKILL-ADR` 决议产出（option A / B 任一）

---

> *Phase M2 content — `state: draft`.*
