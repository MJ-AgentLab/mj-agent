# capabilities/CLAUDE.md

> Capability authoring conventions for `capabilities/<domain>/<slug>/`. Loaded additively
> after root CLAUDE.md when Claude Code works in this subdirectory.
> See root `CLAUDE.md` for repo-wide map + `sdd/constitution.md` for 三柱原则.

## 12-Artifact 套件检查清单（per `mj-agent-refactored-structure.md` §4.5）

每 active capability **必有**：

```
capabilities/<domain>/<slug>/
├── spec.yml                              (REQUIRED;  adapter_coverage 含 tdd-bdd)
├── requirements.md                       (REQUIRED;  含 bdd.examples[] 高风险 REQ)
├── design.md                             (REQUIRED)
├── contracts/                            (REQUIRED;  ≥ 3 contract per capability)
│   ├── <adapter>.contract.yml
│   ├── behavior.feature                  (REQUIRED for 高风险；Gherkin)
│   └── ...
├── tasks.md                              (REQUIRED for active/implementing;  tdd.test_list[])
├── runbook.md                            (REQUIRED for active)
├── trace.yml                             (REQUIRED for active+;  schema v1.2 含 BDD 层)
└── evidence/                             (REQUIRED for active)
    ├── verification/
    ├── reports/
    ├── security/
    ├── runtime/
    ├── postmortems/
    ├── bdd/
    └── tdd/
```

## spec.yml schema 必填字段

详 `sdd/templates/spec.yml.template` + `sdd/traceability.schema.json`：

- `id` (domain.slug;  lowercase + 连字符)
- `name`
- `domain`
- `lifecycle_state` (9 态 enum)
- `archive_state` (5 态 enum)
- `adapter_coverage` (来自 `sdd/adapters/` 已启用列表；含 tdd-bdd)
- `requirements[]` (REQ-NNN list;  含 bdd.examples[] for 高风险)
- `related_decisions` (ADR refs)

## behavior.feature 高风险必填规则

```
priority: critical | high → contracts/behavior.feature MUST exist
                           → REQ 必填 bdd: examples[] 字段（≥ 1 example）
                           → trace.yml bdd 层必填 + automation_status 字段
priority: medium | low   → behavior.feature optional;  contract test 即可
```

详 `sdd/adapters/bdd-tdd.md` §Standards.

## 本子目录最小可执行命令集

```bash
# 校验本 capability spec.yml schema 合规（G1）
uv run python scripts/sdd/check_capability_schema.py <path-to-spec.yml>

# 校验本 capability trace.yml 链路完整（G2/G5）
uv run python scripts/sdd/check_traceability.py <path-to-trace.yml>

# 校验本 capability contracts/ 目录非空 + behavior.feature 存在（G3）
uv run python scripts/sdd/check_contracts.py <path-to-capability>

# 自动生成 INDEX（如新增 / 删除 capability 时）
uv run python scripts/sdd/generate_index.py
```

> Phase M3 Stage C update：G1/G2/G9 real impl landed per `5cd68a6` (M3-FU-G1G2G9-IMPL);
> flipped to BLOCKING per `02b1cc8` (Stage C C-a). G3 `check_contracts.py` 仍 M0 skeleton
> per Stage D 启动状态；Phase M4 real impl tracked separately.

## CI Gates 触及（本 subdir 路径）

- **G1 check_capability_schema** — BLOCKING (Stage C C-a); validates `capabilities/*/*/spec.yml`
- **G2 check_traceability** — BLOCKING; validates `capabilities/*/*/trace.yml` (schema v1.2)
- **G9 generate_index** — BLOCKING (`--check` idempotency); regenerates `capabilities/INDEX.auto.md`
- **G3 check_contracts** — warning (M0 skeleton; Phase M4 real impl)
- Truth source: `.github/workflows/ci.yml` (per-job `continue-on-error` 状态)

## Workflow Routing

| 任务 | Workflow |
|---|---|
| 新 capability | `sdd/workflows/new-capability.md` |
| capability 演进 | `sdd/workflows/evolve-capability.md` |
| capability bugfix | `sdd/workflows/bugfix-drift.md` |
| 跨 capability contract 变更 | `sdd/workflows/cross-capability-change.md` |
| capability 归档 | `sdd/workflows/archive-capability.md` |

## Anti-patterns

- ❌ 在 capability 内引用 archive/ 路径（G14/G15 blocking from Phase M5）
- ❌ contract YAML 字段省略 schema-required 字段（G3 blocking from Phase M3）
- ❌ 高风险 REQ 无 bdd.examples + 无 behavior.feature scenario（G19 blocking from Phase M4）
- ❌ active 态 capability 无 evidence/ 文件（G8 blocking from Phase M4）

## See Also

- 根级：`CLAUDE.md`（repo-wide map）
- `sdd/constitution.md`（三柱原则） + `sdd/lifecycle.md`（9 + 5 状态机） + `sdd/gates.md`
  （CI gate）
- `sdd/templates/`（所有 artifact 的 .template 文件）
- HITL canonical: `policies/ai-agent.md §4` (Canonical 10-Enum — `declared-contract-change`
  enum 覆盖本 subdir contracts/) + `§7` (Pre-flight Verification Discipline)
- A2 hook: `.claude/hooks/stop-claude-md-improver/`

---

> *Phase M0 skeleton — capability 实例填充在 Phase M1（5 pilot capability）.*
