---
type: adr
domain: AGENT
summary: Phase D-3 — Agent_Side v1.1 → v1.2 archive ceremony；§4 EVAL Authoring 完整规范（4 子类 + body 八段 + frontmatter schema）；A8/A11 transitional waiver 延续 Phase E
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: agent
tags:
  - adr
  - documentation
  - eval-framework
  - agent-side
  - track-b
---

# ADR 024: EVAL Framework Spec + Agent_Side v1.2

## Context

mj-agent Agent_Side v1.1（PR #79 Phase C-1a promoted）§4 EVAL Authoring 仅是占位 "沿用 v1.0 §4 全部 TODO Phase 2 项"，无实质内容。同时：

- mj-agent 5 in-source SKILLs（biz-domain-context / qcm-analysis / safe-sql-analysis / query-writing[deprecated] / probe-fixture[fixture]）+ 1 PROMPT（system.md）frontmatter 均无 `eval_references` 字段
- A8/A11 PR 校验门禁（PROMPT/SKILL `state: active` 时 `eval_references` 非空）处于 **transitional waiver** 状态
- `docs/evaluation/` 目录空（无 EVAL 文档）
- `docs/_templates/TEMPLATE_EVAL.md` 已存在（282 行 spec）但未被实际使用

mj-agent runtime 输出错（沉默失败 → 业务决策偏差）只能依赖人工抽检；缺机制化 EVAL 形成 **systemic risk**（per Agent_Side §1 "沉默失败需主动检测"原则）。

Phase D-3 落实 EVAL spec（**不实跑 EVAL runtime**；那是 Phase E）。

## Decision

### 主条款 1：Agent_Side v1.1 → v1.2 archive ceremony

per ADR-017 §5.9 trigger #2（STANDARD 结构性重构）：§4 从占位升级为完整规范属于 substantive 演进，触发 archive ceremony：

- v1.1 → archive `docs/archive/rule/[DEPRECATED]_[STANDARD]_..._Agent_Side_..._v1.1.md`（state: deprecated；archived: 2026-05-09；replaced-by stable path；顶部 `[!warning]` banner）
- v1.2 在原 stable path（per ADR-018 active path stability；filename 不变；`version: v1.2`）

### 主条款 2：§4 EVAL Authoring 完整规范（落 Agent_Side v1.2）

引入 4 EVAL 子类 + body 八段 + frontmatter schema：

**4 子类**：

- `outcome` — 端到端业务结果
- `trajectory` — agent 决策路径
- `component` — 单 skill / prompt 单元
- `integration` — 多 skill 协作

**body 八段**（per docs/INDEX.md TEMPLATE_EVAL 既有定义）：

1. Purpose
2. Eval Design
3. Dataset
4. Judges
5. Baseline
6. Regression Criteria
7. Run History
8. Open Questions

**frontmatter schema**（A9 强制）：

- `eval_kind`, `target_skill`, `target_prompt`, `dataset_path`, `baseline_metric`, `baseline_value`, `regression_threshold`, `judges`

### 主条款 3：A8/A11 transitional waiver 延续 Phase E

**本 ADR 不关闭 A8/A11 transitional waiver**。理由：

- 关闭 waiver 要求 5 SKILLs + 1 PROMPT frontmatter 加 `eval_references`
- 这要求至少 3 个 active EVAL 文档先行（覆盖核心评估）
- EVAL 文档需 EVAL runtime 框架（dataset / judges / metric collection）支撑
- runtime 是 Phase E（Phase 2 业务开发期）工作

**Phase E 关闭 waiver 前置条件**（落 Agent_Side v1.2 §4.6）：

1. `docs/evaluation/` ≥ 3 active EVAL 落地
2. EVAL runtime MVP（dataset / judges / metric / regression detection）
3. 5 SKILLs + 1 PROMPT frontmatter 加 `eval_references`
4. `check_frontmatter.py` 加 SKILL/PROMPT type-conditional A8/A11 校验

### 主条款 4：check_frontmatter.py EVAL 类型条件

`state: active` 的 EVAL 文档强制 frontmatter 字段：

```python
type_specific_required["eval"] = (
    "eval_kind", "dataset_path", "baseline_metric",
    "baseline_value", "regression_threshold",
)
```

`target_skill` / `target_prompt` 之一必填（取决于 `eval_kind`），由 author 选填；不强制 schema 校验。

### 主条款 5：与既有 ADR 关系

- **不 supersede 任何 ADR**
- ADR-011/017-023 全部 sustained 互补
- ADR-014 §决策点 4 边界 artifact 表 sustained（EVAL 默认 `track: agent`）
- ADR-022 C.3.1 sustained（EVAL 不在 4 类专属字段中；本 ADR 单独加 EVAL 类型条件）

## Consequences

### 正面

1. **§4 EVAL spec 可执行** — 未来落首批 EVAL 文档时直接 cite §4；不再"待 Phase 2 补"
2. **4 子类显式定义** — outcome / trajectory / component / integration 边界清晰；EVAL author 选 1
3. **transitional waiver roadmap 显式** — Phase E 关闭条件 4 项前置，每项可逐一推进
4. **check_frontmatter.py EVAL 类型条件** — 未来落 EVAL 文档时 frontmatter schema 自动校验
5. **mj-agent 沉默失败检测可启动** — Phase E EVAL runtime 起首落地后

### 负面

1. **Phase D-3 不实跑 EVAL runtime** — spec / runtime 分阶段；reviewer 看到 spec 但暂无实测验证
2. **TEMPLATE_EVAL.md 字段对齐** — 现有 282 行 template 与本 ADR §4.2 schema 可能有微差；本 PR 不强行对齐（保留 template 现有风格；author 写 EVAL 时以 ADR-024 §4.2 为准；TEMPLATE 后续 align 在 Phase E）
3. **Agent_Side v1.2 archive ceremony 触发 ADR-011 §5.6.2 file-move-step**（已被 ADR-018/019 supersede）— 实际 file 操作走 ADR-019 模式（`[DEPRECATED]_` 前缀 + `archived` + `replaced-by` frontmatter）

### 中性

1. **本 ADR 规模较大但 scope 明确**（仅 spec；不 runtime）
2. **本 PR 自身按 ADR-017 §5.9 判定**：trigger #2 STANDARD 结构性重构（§4 从 4 行 → ~150 行，10× 增长）→ ✅ 触发 archive ceremony；与本 ADR 决策一致 dogfood
3. **mj-agent 文档治理 P0/P1/P2/P3 全项完成** —（含 Phase A-D 全部）；ADR-011/017-024 共 9 个治理 ADR

## Alternatives considered

### A. 推迟 EVAL spec 到 Phase E（与 runtime 同期）

**拒绝原因**：spec / runtime 解耦；spec 是 Phase D-3 收尾合理，runtime 是 Phase 2 业务开发期工作。spec 先行让团队对 EVAL 期望形态有共识，避免 runtime 设计时仓促决策。

### B. 关闭 A8/A11 transitional waiver（Phase D-3 强制 eval_references）

**拒绝原因**：现有 6 in-source canonical（5 SKILLs + 1 PROMPT）frontmatter 不含 `eval_references`；强制要求会破坏现有 active 状态。EVAL runtime 未就位前关闭 waiver 是空规则。

### C. 引入 sample EVAL 文档（如 biz-domain-context outcome eval）

**拒绝原因**：sample EVAL 需 dataset 设计 + baseline 实测；非 spec PR 范畴；Phase E 落首批 EVAL 时再创建。

### D. 不 archive ceremony，仅 in-place edit

**拒绝原因**：违反 ADR-017 §5.9 trigger #2；§4 占位 → 完整规范是 substantive 演进，archive ceremony 保留 v1.1 期权威性供 cite-by-vintage。

### E. 把 EVAL spec 落到独立 STANDARD（如 `[STANDARD]_EVAL_Framework.md`）

**拒绝原因**：(a) Agent_Side §4 已是预留位置；(b) 独立 STANDARD 增加治理复杂度；(c) EVAL 与 SKILL/PROMPT 紧耦合（A8/A11 引用），归 Agent_Side 同框架更内聚。

## References

- 派生源：industry references — LangChain Hub model evals / DSPy assertions / Anthropic Skills 仓 evaluation 模式 / OpenAI Evals framework；mj-system 上游暂无对位 EVAL framework（mj-agent 原生）
- 落地：[[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.2|Agent_Side v1.2]] §4
- 落地（archive）：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1|Agent_Side v1.1（archive）]]
- 关联 ADR：ADR-011/017/018/019/020/021/022/023 全部 sustained 互补
- 关联 GitHub Issue：[#95](https://github.com/MJ-AgentLab/mj-agent/issues/95)
- 后续（Phase E）：
  - 落首批 EVAL 文档（≥ 3 active；docs/evaluation/）
  - EVAL runtime MVP（dataset / judges / metric / regression）
  - 5 SKILLs + 1 PROMPT 加 `eval_references`
  - 关闭 A8/A11 transitional waiver
- TEMPLATE_EVAL.md 后续 align（Phase E；本 PR 不动）
