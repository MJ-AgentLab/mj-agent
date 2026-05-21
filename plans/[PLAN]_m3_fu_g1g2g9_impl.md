---
type: plan
slug: m3-fu-g1g2g9-impl
summary: M3 follow-up plan — implement real G1 (capability-schema) / G2 (traceability) / G9 (generate INDEX) validators replacing M0 skeleton placeholders; M2 Stage E pre-flight reverify 证实 3/3 是 skeleton 而非 real impl；blueprint §6 Phase M2 §3.4 "G1/G2/G9 warning → blocking" 假设其有 real validation logic，但 M0 落地的是 skeleton；M2 promotion impossible until real impl
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

# [PLAN] M3-FU-G1G2G9-IMPL — Real Implementation for G1 / G2 / G9 Validators

> M3 follow-up plan；M3 startup priority；不混入 M3 main work；refines
> `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown.

## §1 Background

M2 Stage E pre-flight dry-run on develop 证实 G1/G2/G9 validators 全部是 M0 skeleton 占位器：

| Gate | Script | Dry-run output | Implementation status |
|---|---|---|---|
| G1 | `scripts/sdd/check_capability_schema.py` | "[skeleton] ... Phase M0 placeholder (G1)" + "Phase M2 will validate" | M0 skeleton；无 validation logic |
| G2 | `scripts/sdd/check_traceability.py` | "[skeleton] ... Phase M0 placeholder (G2/G5)" + "Phase M2/M3 will validate" | M0 skeleton |
| G9 | `scripts/sdd/generate_index.py` | "[skeleton] ... Phase M0 placeholder (G9)" + "Phase M1 will fill in" | M0 skeleton |

3 validators 全部无条件 `return 0` (PASS)；blueprint §6 Phase M2 §3.4 "G1/G2/G9 warning → BLOCKING"
假设 real impl 但 M2 期 Stage A 只新增 6 个 adapter contract validator (V1-V6)；NOT G1/G2/G9
real impl. Stage E E3β 路径接受此 gap：G1/G2/G9 stay warning until real impl 落地.

## §2 Scope

**Included**:

- 实装 `scripts/sdd/check_capability_schema.py` real validation（≥ 80 lines；同 Stage A
  validator 体量）:
  - `capabilities/*/spec.yml` JSON Schema 合规 (per `sdd/traceability.schema.json`)
  - spec.yml `adapter_coverage` 字段含 `bdd-tdd` 校验
  - `--dry-run` / `--capability <path>` / `--all` 三 mode
- 实装 `scripts/sdd/check_traceability.py` real validation（≥ 80 lines）:
  - `capabilities/*/trace.yml` REQ→BDD→CONTRACT→TEST chain 完整性
  - 缺失节点 → WARN (M3 warning) / FAIL (M4 blocking 之后)
  - 同 mode 支持
- 实装 `scripts/sdd/generate_index.py` real generation（≥ 80 lines）:
  - walk `capabilities/*/spec.yml` 提取 capability metadata
  - 生成 `capabilities/INDEX.md` Markdown 表
  - `--check` mode (compare generated vs committed) for G9 idempotency
- 单元测试 in `tests/unit/scripts/sdd/`：3 validator 各 ≥ 3 cases
- 与 `_common.yaml_io` + `_common.discovery` 集成（不重复实装）

**Excluded**:

- 不修改 Stage A 6 adapter validators (M3-FU-VALIDATOR-CONTRACT-ALIGN 独立 plan 处理)
- 不修改 `sdd/traceability.schema.json` (M0 既有；如需扩展走独立 PR)
- 不触达 4 项专属必停 surface 修改
- 不在 CI workflow 立即 toggle (G1/G2/G9 切 blocking 是 M4 工作；M3 stays warning per Stage E
  E3β path)

## §3 Verification

```bash
# 3 validator 实装后跑
uv run python scripts/sdd/check_capability_schema.py --dry-run
uv run python scripts/sdd/check_capability_schema.py --capability capabilities/data-agent/safe-sql/
uv run python scripts/sdd/check_capability_schema.py --all

uv run python scripts/sdd/check_traceability.py --all
uv run python scripts/sdd/generate_index.py --check

# 单元测试
uv run pytest tests/unit/scripts/sdd/test_check_capability_schema.py
uv run pytest tests/unit/scripts/sdd/test_check_traceability.py
uv run pytest tests/unit/scripts/sdd/test_generate_index.py
```

## §4 AC

- [ ] 3 validator scripts 各 ≥ 80 lines real validation logic；不再是 `[skeleton]` 占位
- [ ] 3 validator 跑通 M1 5 pilot capability + M2 Stage C 4 new contracts capability state
- [ ] violation count meaningful (PASS / WARN / FAIL output with reasons)
- [ ] 单元测试覆盖 happy path + missing field + invalid schema + drift detection
- [ ] CI workflow remains warning mode (continue-on-error: true) until M4 (per blueprint M4
      schedule)
- [ ] 与 Stage A 6 adapter validator 一致的 CLI interface (argparse + 3 modes)
- [ ] 独立 PR；commit type `feat(sdd)` or `infra(sdd)`

## §5 估时 / 依赖

- 估时 ~3-6h（3 validator × ~1-2h each + unit tests + integration smoke）
- 依赖：M3 startup；`_common.yaml_io` / `_common.discovery` 已稳定
- PR scope ≤ `scripts/sdd/` + `tests/unit/scripts/sdd/`
- 不依赖 M3-FU-VALIDATOR-CONTRACT-ALIGN（独立 plan；可并行）

## §6 严格守约

- 不预 toggle G1/G2/G9 blocking (M3 仅落 real impl；M4 才 toggle per blueprint schedule)
- 不修改 4 项专属必停 surface
- 不创建新 ADR

---

> *M3 follow-up plan — `state: active`；Stage E pre-flight intercept 触发；M3 startup
> priority；独立小 PR.*
