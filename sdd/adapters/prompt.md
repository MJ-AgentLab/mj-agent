---
type: sdd-adapter
artifact: prompt
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-21
track: agent
ai_visibility: source-of-truth
---

# Adapter: Prompt

> Phase M2 内容化 — Prompt adapter 治理 `src/mj_agent/prompts/system.md` body + frontmatter +
> in-source `skills/*/SKILL.md` body 的 schema invariant contract. §Standards / §BDD Rules /
> §TDD Rules 各段顶部 cross-ref 蓝图 `spec-anchored-calm-lampson.md` 手册 §22.5 Prompt Adapter
> Standards.

## §Scope

**Included** — Prompt adapter 治理：

- `src/mj_agent/prompts/system.md` — body + frontmatter（`version` / `state` /
  `eval_references` 字段）；agent system prompt 静态全量加载入口
- `src/mj_agent/skills/*/SKILL.md` — in-source canonical SKILL body（5 段式 per Agent_Side
  §2.1：Purpose / When to use / Planning workflow / Common patterns / Anti-patterns）；
  frontmatter strip 契约 per Agent_Side §7.5

**Excluded** — 其他 adapter 治理：

- `.claude/skills/mj-agent-*/SKILL.md` — Claude Code workflow SKILL（ADR-013 2-field native
  schema；→ `claude-code-skill` adapter；governance 路径完全不同）
- Tool 注册 / agent graph 拼接 / middleware（→ `langchain-agent` adapter；prompt 内容是
  invariant，行为契约是 agent adapter 的职责）
- Python 加载器实现（`load_prompt` / `load_skill`）→ `python` adapter；prompt adapter 治理
  invariant；loader 行为治理 in python contract

**双 contract pattern** — 同一 SKILL.md 同时受两 adapter 治理（per Agent_Side §7.5 frontmatter
strip 契约）：

- `prompt` adapter — body content invariant（M2 新 `runtime-skill.contract.yml` freeze body
  sha256）
- `runtime-skill` adapter — body 加载 + 与 system prompt 拼接契约
- 两 contract 在不同维度 freeze 同一文件；M3 contract test 实装时按维度分跑

## §Contract Output

`<capability>/contracts/prompt.contract.yml` — per capability one file，描述本 capability 涉及
的 prompt body 的 schema invariant + version freeze + eval reference 集（schema 见
`sdd/templates/contracts/prompt.contract.yml.template`）.

M2 新增 `capabilities/data-agent/llm-provider/contracts/prompt.contract.yml`（Stage C 落地）—
描述 `system.md` v1.8 frozen + body section heads + sha256；与 4 项专属必停的
`prompt-version-bump` gate 配对.

## §Standards

> 本节对应蓝图手册 §22.5 Prompt Adapter Standards.

**Required fields** (contract YAML schema)：

- `prompt_path` — 物理路径（如 `src/mj_agent/prompts/system.md`）
- `version` — frozen 字段；必须与 `prompts/system.md` frontmatter `version` 完全一致；M3
  blocking 校验
- `variables[]` — 模板变量集（mj-agent system.md 当前 `[]` 静态拼接）
- `section_heads[]` — body section 标题清单（如 `["## 角色与任务",
  "## 工具调用约定", ...]`）；M3 contract test 用作 body sha256 之外的 secondary 锁
- `frontmatter_required[]` — frontmatter 必填字段集（`version` / `state` / `eval_references`
  Phase 2+ mandatory per Agent_Side A8）
- `allowed_state_transitions[]` — `state` 字段允许的转换（`draft → active` 要求
  `eval_references` 非空；`active → deprecated` 要求 `superseded_by`）

**`freeze_anchor` 复合对象** — M2 新 contract 用于必停 surface body 双锁：

```yaml
freeze_anchor:
  file: src/mj_agent/prompts/system.md
  version: 1.8                        # frontmatter version 字段值（人类可读锁）
  body_section_heads:                 # body 结构锁（M3 用作 secondary check）
    - "## 角色与任务"
    - "## 工具调用约定"
    - "..."
  content_hash: sha256:<HEX>          # body 内容锁（去 frontmatter 后计算）
  frozen_at: 2026-05-21T...Z
```

**M2 新 prompt.contract.yml 锚定 system.md v1.8** — Stage C 落地：

- `version: 1.8` frozen → 任何 `system.md` `version` 字段变更触发 `prompt-version-bump` 必停
- `content_hash` frozen → body 任何修改（含 typo）触发同必停
- M3 contract test 跑 PASS 条件：当前 `system.md` 的 frontmatter version + body sha256 与
  contract 一致

**`hitl_required[]`** — 仅 gate ID 引用（per Q-A2 Design call 2 clarification）：

```yaml
hitl_required:
  - prompt-version-bump              # canonical 描述在 sdd/gates.md §4
```

**Optional fields**：

- `eval_references[]` — 指向 `tests/eval/component/test_skill_routing.py` 等（M2 期 advisory；
  M4 EVAL framework baseline 后 mandatory per ADR-024）
- `forbidden_phrases[]` — 防 prompt drift "relax 4 stops" 关键短语黑名单（M3+ 落地）
- `regression_eval` — 与 ADR-024 EVAL framework 联动（M4-FU baseline）

## §BDD Rules

> 本节对应蓝图手册 §22.5 BDD Rules（prompt schema invariant tagging — NOT behavior tagging）.

**`@adapter:prompt` 谨慎使用** — prompt 是 schema invariant 而非行为契约（per C4 约定）：

- prompt body 是 LLM 行为的 input；prompt 自身**不是** behavior contract 的载体
- 行为契约（"prompt body 改了 → LLM 选错 tool 顺序"）应该用
  `@adapter:langchain-agent`（agent 是 behavior owner）
- `@adapter:prompt` 限于 frontmatter schema validation + `version` freeze + body sha256 一致
  性 case

**`@adapter:prompt` 何时用** — 限定场景：

- frontmatter schema validation case（`version` 必填；`state: active` 必须有
  `eval_references`）
- `version` freeze drift detection case（contract YAML `version: 1.8` ≠ system.md
  frontmatter）
- body `content_hash` drift detection case（body 被改但 `version` 未 bump）

**`@adapter:prompt` 何时 NOT 用**：

- prose 改动（typo fix / 语法调整 / 章节排版）不为之加 `@adapter:prompt` tag；走
  `prompt-version-bump` 必停手工 review 路径即可
- LLM 行为变化（如 "改 prompt 后 tool 顺序错乱"）→ 用 `@adapter:langchain-agent`
- SKILL body 行为变化 → 用 `@adapter:runtime-skill`（虽然 SKILL.md 同时被 prompt adapter 治
  理 schema 一致性）

**`@adapter:prompt` + `@hitl` 必然双标签** — prompt 触达 4 项专属必停的 `prompt-version-bump`
gate；任何 `@adapter:prompt` scenario 都隐含 hitl 信号.

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:prompt @hitl
Scenario: prompt.contract.yml drifts when system.md version is bumped without YAML update
  Given prompts/system.md frontmatter has version: 1.9
  And prompt.contract.yml freeze_anchor.version is 1.8
  When check_prompt_contracts.py is run
  Then the result is FAIL
  And the error message references prompt-version-bump gate (sdd/gates.md §4)
```

## §TDD Rules

> 本节对应蓝图手册 §22.5 TDD Rules（schema-layer test-first；regression EVAL 是 future）.

**Contract-test-first 限于 frontmatter schema 层**：

- `prompt.contract.yml` 的 `version` / `section_heads[]` / `content_hash` 字段变更 → 必先有
  failing test
- M3 contract test pattern：解析 system.md frontmatter + 计算 body sha256 + 比对 contract
- 不要求 prompt prose 改动也跑 test-first（prose 改动走 `prompt-version-bump` 必停手工 review
  + EVAL regression in M4+）

**Prompt regression case 走 EVAL framework**（per ADR-024 EVAL framework 联动）：

- M2 期 EVAL framework 未 baseline（M4-FU `mj-agent-runtime-eval-baseline` skill 实测）；
  test-first 软模式 per RD10=C
- body change → `version` bump → EVAL regression suite 触发
- M4 后 PR gate A8 强制 `state: active` 时 `eval_references` 非空

**Red-Green-Refactor 软模式 + EVAL 联动路径**：

1. M2-M3：`check_prompt_contracts.py` 跑 schema + freeze 校验（PASS = frontmatter 合 contract）
2. M4：EVAL framework baseline 落地 → A8 强制 `eval_references` 非空
3. M5+：body 改动触发 EVAL regression（component-level skill routing test）

**`_common.frontmatter` 接口** — Stage A 实装（python-frontmatter 包装）：

```python
# scripts/sdd/_common/frontmatter.py 公开符号（schema layer 用）：

load_frontmatter(file_path: Path) -> dict | None
    # 安全加载 YAML frontmatter；缺失或格式错误返回 None

strip_frontmatter(content: str) -> str
    # 去 frontmatter（per Agent_Side §7.5 contract）；body 计算 sha256 时用
```

**G28 联动** — `prompt.contract.yml` `version` / `content_hash` / `section_heads[]` 任一字段
变更 → 必须配套 `tests/contracts/<capability>/test_prompt_contract.py` 内 failing→green 转变.

## §CI Gate

**Script gate**: `scripts/sdd/check_prompt_contracts.py`

- **Phase**: M2 warning / **M3 blocking**（per `sdd/gates.md` G3 / G4 切换节奏）
- **Triggers**: `capabilities/*/contracts/prompt.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（`version` mismatch / `content_hash` drift /
  缺失 `eval_references`）
- **Implementation**: `_common.frontmatter` 加载 + `strip_frontmatter` 后 sha256 + 比对
  contract freeze_anchor

**Baseline noise** — Stage C 后 V3 实测 PASS（`system.md` v1.8 frozen + `llm-provider/
prompt.contract.yml` 落地）；M2 期 warning mode 下预期 0 noise.

**Manual HITL gate** (permanent blocking；M2 不可 script 完全 auto-detect)：

- Gate ID: `prompt-version-bump`（per `sdd/gates.md` §4）
- Triggers: 任意 `src/mj_agent/prompts/system.md` body / frontmatter `version` 字段变更
- Detection: PR reviewer mandatory check + script `check_prompt_contracts.py` 提前预警
  drift
- Rationale: prompt body 改动可能引入 LLM 行为 regression 但 schema 仍合规；script 看不出语义
  drift；必须 human review
- Future: M5+ 视 EVAL framework 成熟度可考虑加 EVAL-based auto-detect；M2 不在范围

**M2 → M3 切换条件**：

- Stage C 4 新 contract 中的 `llm-provider/prompt.contract.yml` PASS
- `_common.frontmatter` 接口稳定
- `prompt-version-bump` gate 在 `gates.md` §4 完整定义（C5 落地后；M3-FU-HITL-ENUM）

---

> *Phase M2 content — `state: draft`.*
