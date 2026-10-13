# capabilities/AGENTS.md

> Codex 局部约束，与根 AGENTS.md 共同生效；规则正文仍在项目 kernel。

## Structure obligations

- Every active capability carries the 12-artifact suite (spec.yml / requirements.md /
  design.md / contracts/ / tasks.md / runbook.md / trace.yml / evidence/); schemas live in
  `sdd/templates/` + `sdd/traceability.schema.json`. Copy templates — do not improvise fields.
- Contract YAML must carry all schema-required fields (gate G3); high-risk REQs need
  `bdd.examples[]` + `contracts/behavior.feature` (gate G19).
- Never reference `archive/**` paths from active capability files (gates G14/G15).

## 风险分类与冻结

兼容合同补齐与基线内实现自主；breaking承诺、跨域接受标准或权限变化按 `policies/ai-agent.md` §4先Owner决定。路径命中不自动审批。

infra合同 `infrastructure/mcp-server-governance/contracts/development-skill.contract.yml` 锁8技能。按header算法先复算旧description/body hash，保持schema后成组更新新hash/section heads/frozen_at；改变信任、权限或治理标准须具名决定。冻结一致性不认证授权或实际宿主加载。

## Verification (either tool, from repo root)

```bash
uv run python scripts/sdd/check_capability_schema.py --all
uv run python scripts/sdd/check_traceability.py --all
uv run python scripts/sdd/check_contracts.py --all
uv run python scripts/sdd/generate_index.py   # after adding/removing a capability
```

## See also

- Root `AGENTS.md` (roster + self-enforced boundaries)
  (Claude-specific working notes, same layer)
- `sdd/constitution.md` · `sdd/lifecycle.md` · `sdd/gates.md` · `sdd/workflows/` (task routing)
- `policies/ai-agent.md` §4 (canonical 10-enum) + §7 (pre-flight verification discipline)

## Authoring details

spec.yml 字段与 suite 以 `sdd/templates/` 为准；保留 adapter_coverage 现有 schema。高风险 REQ 必有 bdd.examples、behavior.feature 及 trace BDD automation_status。工作流见 `sdd/workflows/{new-capability,evolve-capability,bugfix-drift,cross-capability-change,archive-capability}.md`。gate 姿态以 CI 实况为准，不复制旧时点计数。
