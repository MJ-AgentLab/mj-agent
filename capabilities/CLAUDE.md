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

> Phase M0 — 上述脚本为 skeleton；Phase M1 起逐步实现.

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

- `sdd/constitution.md`（三柱原则） + `sdd/lifecycle.md`（9 + 5 状态机） + `sdd/gates.md`
  （CI gate）
- `sdd/templates/`（所有 artifact 的 .template 文件）

---

> *Phase M0 skeleton — capability 实例填充在 Phase M1（5 pilot capability）.*
