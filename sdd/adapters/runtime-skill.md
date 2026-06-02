---
type: sdd-adapter
artifact: runtime-skill
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-21
track: agent
ai_visibility: source-of-truth
---

# Adapter: Runtime Skill (in-source canonical)

> Phase M2 内容化 — Runtime Skill adapter 治理 `src/mj_agent/skills/*` in-source canonical
> SKILL.md 的 body 加载 + 与 system prompt 拼接契约 + frontmatter strip 硬约束.
> §Standards / §BDD Rules / §TDD Rules 各段顶部 cross-ref 蓝图 `spec-anchored-calm-lampson.md`
> 手册 §22.6 Runtime Skill Adapter Standards.

## §Scope

**Included** — Runtime Skill adapter 治理：

- `src/mj_agent/skills/<name>/SKILL.md` — 9 in-source canonical SKILL（MVP 启用 3 个：
  `biz-domain-context` / `qcm-analysis` / `safe-sql-analysis`）
- SKILL body 加载 via `src.mj_agent.skills.load_skill`（python-frontmatter 包装；返回 body
  string，frontmatter 已 strip per Agent_Side §7.5）
- 与 system prompt 拼接行为：`agent.py` 的 `_build_system_prompt()` 顺序拼接
  `prompts/system.md` body + `_ACTIVE_SKILLS` 列出的 SKILL body
- 多 SKILL 集合契约：同一 capability 可同时 freeze 多个 SKILL（如 `biz-catalog`
  capability freeze `biz-domain-context` + `qcm-analysis` 两 SKILL）

**Excluded** — 其他 adapter 治理：

- `.claude/skills/mj-agent-*/SKILL.md` — Claude Code workflow SKILL（→ `claude-code-skill`
  adapter；ADR-013 native 2-field schema；governance 路径完全不同）
- SKILL.md frontmatter schema validation（→ `prompt` adapter；schema invariant 维度）
- `load_skill` 函数本身的 Python 公开签名（→ `python` adapter；本 adapter 只管"调用 loader
  得到 body string 后的拼接行为"）

**双 contract pattern**（同一 SKILL.md 受两 adapter 治理；per `prompt.md §Scope` 互引）：

- `prompt` adapter — body content invariant（schema layer；`prompt.contract.yml`）
- `runtime-skill` adapter — body 加载 + 与 system prompt 拼接行为（`runtime-skill.contract.yml`）
- 两 contract 不同维度 freeze 同一文件；M3 contract test 实装时按 contract 分跑

## §Contract Output

`<capability>/contracts/runtime-skill.contract.yml` — per capability one file，描述本 capability
涉及的 in-source SKILL 集合（schema 见 `sdd/templates/contracts/runtime-skill.contract.yml.
template`）.

M2 Stage C 新增 2 contract：

- `capabilities/data-agent/safe-sql/contracts/runtime-skill.contract.yml` — 单 SKILL
  （`safe-sql-analysis`）
- `capabilities/data-agent/biz-catalog/contracts/runtime-skill.contract.yml` — 双 SKILL
  （`biz-domain-context` + `qcm-analysis` 各 freeze frontmatter + body sha256）

## §Standards

> 本节对应蓝图手册 §22.6 Runtime Skill Adapter Standards.

**Required fields** (contract YAML schema)：

- `skills[]` — SKILL 列表（M2 evolution；template M0 用 `skill_path` 单 SKILL 形式，M2 起以
  `skills[]` 集合形式为 canonical 支持多 SKILL freeze）；每条包含：
  - `file` — 物理路径（如 `src/mj_agent/skills/safe-sql-analysis/SKILL.md`）
  - `version` — frozen frontmatter `version` 字段值
  - `body_section_heads[]` — body sections（M2/M4 current canonical = **6 段**：`## Purpose` /
    `## When to use` / `## Planning workflow` / `## Common patterns` / `## Anti-patterns` /
    `## Related`）。`## Related` 是 allowed 第 6 section，且当前已被 runtime-skill contracts
    冻结（contracts 是 source of truth）。旧 Agent_Side §2.1 的 5 段式表述是 M5-archive-bound
    legacy wording，不再 override 当前 contract-frozen 6-section reality（per E-4-PR4；M3-FU
    `skill-5segment-normalize` Option B resolution）
  - `content_hash: sha256:<HEX>` — body sha256（去 frontmatter 后计算）
  - `frozen_at: <ISO timestamp>`
  - `variables[]` — 模板变量集（mj-agent SKILL 当前 `[]` 静态拼接）
  - `triggers_visible[]` — frontmatter `triggers_visible` 字段镜像
  - `used_by_agent: true` — 是否在 `_ACTIVE_SKILLS` 列表中（M2 期 MVP 3 SKILL 都是）
- `frontmatter_strip_contract: true` — loader 必须 strip frontmatter（per Agent_Side §7.5；硬
  约束）
- `loader: load_skill` — `src.mj_agent.skills` package 的 loader 函数名（cross-validate with
  `python.contract.yml`）

**Optional fields**：

- `cross_skill_refs[]` — SKILL 间互引（如 `safe-sql-analysis` 引 `biz-domain-context`）
- `character_budget` — LLM context budget 上限（M3+ 落地；防 system prompt 膨胀）
- `eval_references[]` — Phase 2+ mandatory per Agent_Side A8（M2 advisory；M4 EVAL framework
  baseline 后 mandatory per ADR-024）
- `allowed_state_transitions[]` — `state` 字段允许的转换（`draft → active` 要求
  `eval_references` 非空）

**`hitl_required[]`** — 仅 gate ID 引用（hyphen canonical per C5）：

```yaml
hitl_required:
  - runtime-skill-content-change       # 任何 SKILL body / frontmatter 变更触发
```

**Frontmatter Strip 契约（硬约束）** — 任何代码绕过 `load_skill` 直接 `open().read()` SKILL.md
**违反契约** → A11 PR gate（M3 起 blocking）；运行时 LLM input 必须是 strip 后的 body string，
不能包含 frontmatter YAML 块.

```python
# 正确（符合契约）：
from src.mj_agent.skills import load_skill
body = load_skill("safe-sql-analysis")  # frontmatter 已 strip

# 错误（违反契约）：
body = open("src/mj_agent/skills/safe-sql-analysis/SKILL.md").read()  # 含 frontmatter
```

## §BDD Rules

> 本节对应蓝图手册 §22.6 BDD Rules（runtime SKILL body 加载 + 拼接 + loader 行为 tagging）.

**`@adapter:runtime-skill` 何时用** — SKILL body 加载 + 拼接行为 scenario：

- SKILL body 通过 `load_skill` 加载后是否 strip frontmatter（loader 行为验证）
- system prompt 拼接顺序（`prompts/system.md` body + `_ACTIVE_SKILLS` 顺序的 SKILL body）
- SKILL body 修改是否触发预期的 LLM 行为变化（与 EVAL framework 联动；M4+）

**`@adapter:runtime-skill` 何时 NOT 用** — 避免与 prompt adapter 重复：

- SKILL frontmatter schema validation（如 `version` 字段必填）→ 用 `@adapter:prompt`
- 纯 SKILL prose 改动（typo / 排版）→ 不加 `@adapter:runtime-skill` tag；走
  `runtime-skill-content-change` 必停手工 review
- `load_skill` 函数本身的签名 / 异常 / 实现 → 用 `@adapter:python`

**`@adapter:runtime-skill` + `@hitl` 必然双标签** — 任何 SKILL body / frontmatter 改动必然触
达 `runtime-skill-content-change` 必停 gate；scenario 自带 hitl 信号.

**`@risk:high` 配套 BDD 必填** — M2 MVP 的 3 SKILL 都属 high risk（直接进 LLM input；语义
drift 即业务 risk）；M3-M4 自动化阈值 100% 目标（per RD9=B + `bdd-tdd.md` §Automation Strategy）.

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:runtime-skill @hitl @risk:high
Scenario: load_skill strips frontmatter before LLM consumption
  Given src/mj_agent/skills/safe-sql-analysis/SKILL.md has frontmatter "version: 1.2"
  When agent._build_system_prompt() concatenates the SKILL body
  Then the LLM input does not contain "version: 1.2" YAML key
  And the LLM input contains the body after the frontmatter block
```

## §TDD Rules

> 本节对应蓝图手册 §22.6 TDD Rules（runtime SKILL contract-test-first + EVAL future）.

**Contract-test-first 限于 schema layer**：

- `runtime-skill.contract.yml` 的 `skills[].version` / `content_hash` / `body_section_heads`
  字段变更 → 必先有 failing test
- 不要求 SKILL prose 改动跑 test-first（走 `runtime-skill-content-change` 必停 + M4+ EVAL
  regression）

**Body content_hash 双锁**：

- frontmatter `version` 字段值 + body sha256 二者必须同步变化
- `version` bump 但 body sha256 不变 → drift；`version` 不变但 body sha256 变 → drift
- M3 contract test 校验：解析 frontmatter → 取 version + 计算 body sha256 → 比对 contract
  freeze_anchor

**`_common.frontmatter` 共享接口** — 与 prompt adapter 共用 Stage A 实装：

```python
# scripts/sdd/_common/frontmatter.py 公开符号（runtime-skill + prompt adapter 共用）：

load_frontmatter(file_path: Path) -> dict | None
    # 安全加载 YAML frontmatter；缺失 / 格式错误返回 None

strip_frontmatter(content: str) -> str
    # 去 frontmatter 返回 body string；body sha256 计算的输入
```

**Red-Green-Refactor 软模式 (RD10=C) + EVAL 联动**：

- M2-M3：schema-layer test（`check_runtime_expected.py` M2 skeleton；schema 部分由 Stage A 的
  ast-based check 已覆盖；M4 完整实装行为层）
- M4：EVAL framework baseline 落地 → SKILL body 改动触发 EVAL regression（component-level
  skill routing test）
- M5+：runtime SKILL `state: active` 转换要求 `eval_references[]` 非空（per Agent_Side A8）

**G28 contract-test-first blocking 联动** (M3 起)：

- 任意 `runtime-skill.contract.yml` `skills[]` 列表增删 / `content_hash` 变更 → 必须配套
  `tests/contracts/<capability>/test_runtime_skill_contract.py` 内 failing→green 转变

## §CI Gate

**Script gate**: `scripts/sdd/check_runtime_expected.py`

- **Phase**: M2 **skeleton**（仅 schema layer 部分由 Stage A ast-based check 已覆盖）；M3
  warning；M4 完整实装行为层（runtime SKILL 加载顺序 + loader 调用路径反向验证）
- **Triggers**: `capabilities/*/contracts/runtime-skill.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（`version` mismatch / `content_hash` drift /
  缺失 SKILL / `frontmatter_strip_contract` 违反）
- **Implementation**: `_common.frontmatter` + body sha256 + `ast_helpers.parse_module_safe`
  扫描 `agent.py` 验证 `load_skill` 是 SKILL 的唯一加载路径

**Baseline noise** — M2 期 V2 smoke-only（Stage C 新增 2 contract 后 V2 升级 PASS 实测）；M2
warning mode 下预期 0 noise.

**Manual HITL gate**（permanent blocking；M2 不可 script 完全 auto-detect）：

- Gate ID: `runtime-skill-content-change`（per `sdd/gates.md` §4）
- Triggers: 任意 `src/mj_agent/skills/*/SKILL.md` body 或 frontmatter 变更
- Detection: PR reviewer mandatory check + script `check_runtime_expected.py` 提前预警
  `content_hash` drift
- Rationale: SKILL body 改动可能改变 LLM 决策路径但 schema 仍合规；script 看不出语义 drift；
  必须 human review + M4+ EVAL regression 配套
- Future: M5+ 视 EVAL framework 成熟度可考虑加 EVAL-based auto-detect；M2 不在范围

**M2 → M3 切换条件**：

- Stage C 2 新 contract（`safe-sql/runtime-skill.contract.yml` + `biz-catalog/runtime-skill.
  contract.yml`）schema layer PASS
- `_common.frontmatter` 接口稳定（与 prompt adapter 共用）
- `runtime-skill-content-change` gate 在 `gates.md` §4 完整定义（C5 落地后；M3-FU-HITL-ENUM）

---

> *Phase M2 content — `state: draft`.*
