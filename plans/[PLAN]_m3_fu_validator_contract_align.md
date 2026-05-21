---
type: plan
slug: m3-fu-validator-contract-align
summary: M3 follow-up plan — fix Stage A 6 adapter validator vs Stage B adapter doc canonical schema drift surfaced in M2 Stage E pre-outline reverify; V3 expects bare hex content_hash but Stage C contracts use sha256:<hex> prefix per Stage B canonical; cross-validator consistency fix
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

# [PLAN] M3-FU-VALIDATOR-CONTRACT-ALIGN — Stage A Validator vs Stage B Canonical Schema Drift

> M3 follow-up plan；M3 startup；独立小 PR；refines `plans/[PLAN]_spec_anchored_refactor.md`
> §M3 Task Breakdown；与 M3-FU-V4-VALIDATOR-INVESTIGATE / M3-FU-G1G2G9-IMPL 同期 validator
> family work.

## §1 Background

M2 Stage E pre-outline reverify 跑 V3 prompt validator against #3 Stage C contract（commit
`5b54f51`）发现 schema 格式 drift：

```
[FAIL] src/mj_agent/prompts/system.md: BODY CONTENT HASH DRIFT — contract anchored
'sha256:994d4a2d7...' but actual is '994d4a2d7fd3677f...' (prompt-version-bump 必停
surface drifted; STOP + HITL; investigate)
```

Root cause: Stage A 验证器 (`check_prompt_contracts.py` L94-97) 做直接字符串比较；期望
bare hex；Stage C 4 contracts 全部使用 `sha256:<hex>` prefix (per Stage B adapter doc
canonical convention).

**Schema disagreement matrix**:

| 字段 | Stage A validator expects | Stage B adapter doc canonical (Stage C uses) | drift |
|---|---|---|---|
| `content_hash` prefix | bare hex (no prefix) | `sha256:<hex>` prefix | ✗ |
| body section heads 字段名 | `body_section_names` | `body_section_heads` | ✗ |

Stage A 在 Stage B canonical 落地之前实装；validator 没追上 canonical 演进. M2 Stage C 收尾
不修改 Stage A（避免 commit history rewrite）；M3 独立 PR 修复 validator 让 schema 对齐.

## §2 Scope

**Included**:

- **V3 `check_prompt_contracts.py` 修复**:
  - `content_hash` field：accept `sha256:<hex>` 或 `<hex>` 双格式（strip "sha256:" prefix
    before compare；canonical 为 prefix form per Stage B）
  - `body_section_heads` field：accept 此名 (per Stage B canonical) OR migrate from existing
    `body_section_names`（双名兼容期 ~2 phase；M5 normalize 单名）
- **V1 `check_python_contracts.py` 同步审查**:
  - 当前 M1 python contract 不含 `content_hash` 字段；但 M3-FU-RUNTIME-SKILL-VALIDATOR
    实装时 share fix logic
- **V4 `check_claude_skill_contracts.py` 同步审查** (与 M3-FU-V4-VALIDATOR-INVESTIGATE 协调):
  - Stage C #4 contract 含 `description_hash` + `body_content_hash` 双 hash 字段；都用
    `sha256:<hex>` prefix
  - V4 fix 时 incorporate this canonical prefix format
- **V5 `check_docker_contracts.py` 同步审查**:
  - 当前 M1 docker contracts 不含 content_hash（freeze_anchor 是 string path style）；预
    M3+ 可能扩展时 share fix
- **Cross-validator consistency test** in `tests/unit/scripts/sdd/test_cross_validator_consistency.py`:
  - 验证所有 hash field 解析采用统一 helper (e.g., `_common.hash_compare.strip_prefix_compare`)
  - 验证 `body_section_*` field 名称跨 validator 一致

**Excluded**:

- 不修改 Stage C 4 contracts（per commit history closure；canonical 不动）
- 不修改 Stage B 7 adapter docs（canonical 不动）
- 不修改 V2 `check_agent_contracts.py`（smoke-only；无 content_hash 解析触发）
- 不修改 V6 `check_runtime_expected.py`（skeleton；M4 实装时统一 fix）
- 不触达 4 项专属必停 surface

## §3 Verification

```bash
# 修复后跑 V3 against Stage C #3
uv run python scripts/sdd/check_prompt_contracts.py --capability capabilities/data-agent/llm-provider/
# 期望 [PASS] verified instead of FAIL

# V4 (after M3-FU-V4-VALIDATOR-INVESTIGATE merged) against Stage C #4
uv run python scripts/sdd/check_claude_skill_contracts.py --capability capabilities/infrastructure/mcp-server-governance/
# 期望 6/6 SKILLs verified per ADR-013 (not 34 spurious WARN)

# Cross-validator consistency test
uv run pytest tests/unit/scripts/sdd/test_cross_validator_consistency.py
```

## §4 AC

- [ ] V3 跑通 Stage C #3 (llm-provider/prompt.contract.yml) PASS (不再 FAIL on content_hash)
- [ ] V3 双格式兼容（`sha256:<hex>` 和 `<hex>` 都接受）；canonical 为 prefix form
- [ ] `body_section_heads` field 在 V3 (and applicable V4/V5) 被 accept
- [ ] Cross-validator consistency test green：所有 hash field 解析统一 helper
- [ ] Stage C 4 contracts 全部 validator PASS (V3 + V4 fixed + 未来 M3-FU-RUNTIME-SKILL-
      VALIDATOR for #1/#2)
- [ ] 单元测试 ≥ 5 cases（含 prefix / no-prefix / mixed case / field rename / consistency）
- [ ] 独立 PR；commit type `fix(sdd)`

## §5 估时 / 依赖

- 估时 ~2-3h (validator code fix + unit tests + cross-validator consistency test)
- 依赖：M3 startup；可与 M3-FU-V4-VALIDATOR-INVESTIGATE 并行（互不阻塞）
- PR scope ≤ `scripts/sdd/check_*.py` + `tests/unit/scripts/sdd/`

## §6 严格守约

- 不修改 Stage C 4 contracts (合法已 committed；canonical per Stage B)
- 不修改 Stage B 7 adapter docs (canonical 不动)
- 不预 toggle 任何 gate 到 blocking (M4 blocking schedule per blueprint)
- 不触达 4 项专属必停 surface

---

> *M3 follow-up plan — `state: active`；Stage E pre-outline reverify 触发；M3 startup；
> 独立小 PR.*
