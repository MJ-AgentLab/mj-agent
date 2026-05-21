---
type: plan
slug: m3-fu-runtime-skill-validator
summary: M3 follow-up plan — implement scripts/sdd/check_runtime_skill_contracts.py validator for runtime-skill.contract.yml; M2 Stage C batch 1 启动前 spot-check 发现现有 check_runtime_expected.py 是 docker-only validator，runtime-skill 暂无专属 validator
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-05-21
track: shared
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-RUNTIME-SKILL-VALIDATOR — Runtime-Skill Contract Validator

> M3 follow-up plan；M3 startup 后独立小 PR；不混入 M3 main work；refines
> `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown.

## §1 Background

M2 Stage C batch 1 启动前 spot-check（Path β confirmed）发现：

- `scripts/sdd/check_runtime_expected.py`（Stage A 实装）实际职责是验证 docker family
  `capabilities/*/contracts/runtime.expected.yaml`（注意 `.yaml` 后缀；属 docker-container
  adapter triple-contract 中第 3 contract）
- `runtime-skill.contract.yml`（Stage C 新增 2 contract: safe-sql + biz-catalog）与
  `runtime.expected.yaml` 是完全不同 schema（前者：SKILL.md `content_hash` freeze +
  frontmatter strip；后者：ports / volumes / networks / depends_on graph）
- → runtime-skill 当前**无专属 validator**；Stage C batch 1 §Verification 临时降级为
  "yaml.safe_load 合法性 + git diff 必停 surface 空集" 双 gate；不调用任何 validator

## §2 Scope

**Included**:

- 新建 `scripts/sdd/check_runtime_skill_contracts.py`（~80-150 lines；同 Stage A 6 validator
  代码体量）
- Schema validation：`contract_id` / `adapter` / `skills[]` / `frontmatter_strip_contract` /
  `loader` / `hitl_required[]` / `allowed_state_transitions[]` 字段必填检查
- Per-SKILL validation：`file` 存在 / `version` 与 SKILL.md frontmatter 一致（**string-exact
  比较**：不 strip "v" 前缀，不 normalize；如 SKILL frontmatter `version: v0.2` 与 contract
  `version: v0.2` 必须字符级一致；任何 v 前缀增删 / 大小写变化 → FAIL，视为 explicit
  version semantic 修改而非 cosmetic normalization）/ `content_hash` 与 body sha256（按
  canonical 算法：strip frontmatter via regex + LF 归一化）一致 / `body_section_heads[]` 与
  实际 SKILL.md headers 一致 / `triggers_visible[]` 镜像 frontmatter
- 与 `_common.frontmatter` + `_common.yaml_io` 集成；不重复实装解析逻辑
- 单元测试 in `tests/unit/scripts/sdd/test_check_runtime_skill_contracts.py`：happy path +
  `content_hash` drift detection + `frontmatter_strip_contract` 违反 case + missing
  `skills[]` entry

**Excluded**:

- 不修改 7 adapter doc
- 不修改 `check_runtime_expected.py`（保留 docker-only validator scope）
- 不触达 4 项专属必停 surface 修改（仅 read 校验）
- 不集成 EVAL framework（推到 M4-FU 单独 task）
- 不修改 Stage C 落地的 2 contract YAML（contract 是 fixture，validator 反向校验）

## §3 Verification

```bash
# Validator 实装后
uv run python scripts/sdd/check_runtime_skill_contracts.py --dry-run
uv run python scripts/sdd/check_runtime_skill_contracts.py --capability \
  capabilities/data-agent/safe-sql/
uv run python scripts/sdd/check_runtime_skill_contracts.py --capability \
  capabilities/data-agent/biz-catalog/
uv run python scripts/sdd/check_runtime_skill_contracts.py --all

# 单元测试
uv run pytest tests/unit/scripts/sdd/test_check_runtime_skill_contracts.py -v
```

## §4 AC

- [ ] `scripts/sdd/check_runtime_skill_contracts.py` ≥ 80 lines；含真实 validation logic
      （不是 `[skeleton]` 占位）
- [ ] 跑通 M2 Stage C 落地的 2 个 runtime-skill.contract.yml（safe-sql + biz-catalog）PASS
- [ ] 与 `_common.frontmatter` API 一致；不重复实装 strip_frontmatter / load_frontmatter
- [ ] `content_hash` drift detection PASS（修改 SKILL.md body → validator 应 FAIL；含 LF
      归一化 deterministic）
- [ ] 单元测试覆盖 ≥ 5 case（happy path + content_hash drift + frontmatter strip 违反 +
      missing skill + version string-exact drift 如 `v0.2 → 0.2` should FAIL）
- [ ] CI workflow 接入：M3 warning / M4 blocking（per gates.md 节奏；与其他 validator 一致）
- [ ] 独立小 PR；commit type `feat(sdd)` 或 `infra(sdd)`

## §5 估时 / 依赖

- 估时 ~3-4h（validator code + unit test + CI 接入）
- 依赖：M3 startup；M2 Stage C 落地的 2 runtime-skill.contract.yml 作 test fixture
- PR scope ≤ `scripts/sdd/` + `tests/unit/scripts/sdd/` + `.github/workflows/ci.yml`

## §6 严格守约

- 不修改 7 adapter doc / 4 项专属必停 surface / `check_runtime_expected.py`
- 不创建新 ADR（validator 实装不构成 architectural decision；schema 已在 adapter doc canonical）
- 不集成 EVAL framework（推到 M4-FU）

---

> *M3 follow-up plan — `state: active`；M2 Stage C 后置；M3 startup 后处理；独立小 PR.*
