---
type: plan
slug: m3-fu-runtime-skill-validator
summary: M3 follow-up plan — implement scripts/sdd/check_runtime_skill_contracts.py validator for runtime-skill.contract.yml; M2 Stage C batch 1 启动前 spot-check 发现现有 check_runtime_expected.py 是 docker-only validator，runtime-skill 暂无专属 validator
state: completed
version: 0.2
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

**Accumulated AC from Stage C closure** (2026-05-21；per #1/#2/#3/#4 Gate-2 observations):

- `hitl_required[]` must be hyphen canonical only (per C5；e.g., `runtime-skill-content-change`
  NOT `runtime_skill_content_change`)
- `version` field string-exact comparison (no v-prefix strip / no normalize；详上 §Included)
- **9-field prose-like exclude list**：M3 validator MUST NOT require frozen values for these
  prose-like / canonical-by-purpose frontmatter fields: `type` / `domain` / `summary` /
  `owner` / `created` / `updated` / `track` / `eval_references` / `supersedes`；validator
  scope 限定 freeze-relevant schema invariant fields only；prose fields 由 body content_hash
  间接覆盖（per #3 broadcast）
- `frontmatter_freeze` 字段 (new schema field from #3 prompt contract)：validator 支持
  explicit frozen values for non-version freeze-relevant subset；string-exact comparison
- 中文 / non-ASCII section heads UTF-8 透明：YAML literal scalar handles transparently；
  validator AC 隐含支持，不需 special handling
- `description_hash` (claude-skill family Option B)：validator 计算 SHA-256 over description
  string UTF-8 + 比对 contract YAML `skills[].description_hash`；与 body `content_hash` 算法
  并存但不混用 (input source 不同)

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

## §7 Resolution（M3 Stage A 闭环）

新增 `scripts/sdd/check_runtime_skill_contracts.py`（~210 lines；含真实 validation
logic）。Stage C 落地的 2 个 runtime-skill.contract.yml（safe-sql + biz-catalog；
覆盖 3 个 in-source SKILLs）全部 PASS。

实装亮点：
- 复用 `_common.frontmatter`（parse_frontmatter / body_sha256 / extract_headings）
  + P0-2 新加的 `content_hash_matches`（`sha256:` 前缀兼容；V7 是首个 V3 之外的
  consumer，证实 helper 跨 validator 可复用）。
- `_validate_skill_entry` 改用 shared summary 参数（per `Summary.merge()` 是
  counts-only 设计；nested summary 会丢失 per-skill messages）。
- 10 单元测试覆盖：happy / content_hash drift / frontmatter_strip_contract 违反 /
  空 skills[] / version v-prefix string-exact drift (v0.1 vs 0.1) / state mismatch /
  missing required field / missing file / section heads warn-only / wrong contract_id
  （≥ 5 per AC §4，超额）。
- CI workflow V7 step 在 V6 之后；warning mode (`continue-on-error: true`)；M4 strict
  per gate matrix。

V7 输出：**3 PASS / 0 WARN / 0 FAIL** against 2 contracts × 3 SKILLs。

V4 Mode B（claude-skill contract-driven hash enforcement）保持 future-scope；
V6 runtime probe（M4 docker subprocess probe）保持 future-scope；本 plan 不扩展。

详细 evidence: [[capabilities/data-agent/safe-sql/evidence/reports/v7-runtime-skill-validator-landing]].

---

> *M3 follow-up plan — `state: completed`；M3 Stage A 闭环；独立 commit `feat(sdd):
> land V7 runtime-skill validator (M3-FU-RUNTIME-SKILL-VALIDATOR)`.*
