# capabilities/AGENTS.md

> Tool-neutral local constraints for `capabilities/<domain>/<slug>/` — binds every AI agent
> working here (Claude Code, Codex, any future authorized agent; roster in root `AGENTS.md`).
> Codex discovers this file hierarchically (root → cwd); Claude Code imports it via the
> sibling `capabilities/CLAUDE.md`. Rules live once in the project kernel (`sdd/` +
> `policies/` + capability contracts) — this file only points.

## Structure obligations

- Every active capability carries the 12-artifact suite (spec.yml / requirements.md /
  design.md / contracts/ / tasks.md / runbook.md / trace.yml / evidence/); schemas live in
  `sdd/templates/` + `sdd/traceability.schema.json`. Copy templates — do not improvise fields.
- Contract YAML must carry all schema-required fields (gate G3); high-risk REQs need
  `bdd.examples[]` + `contracts/behavior.feature` (gate G19).
- Never reference `archive/**` paths from active capability files (gates G14/G15).

## Owner stop points (OWNER_APPROVAL_REQUIRED)

- **Declared contract change** — semantic changes to `contracts/*.contract.yml` consumed
  across capabilities hit the canonical enum `declared-contract-change`
  (`policies/ai-agent.md` §4); stop and obtain Owner sign-off before editing.
- **Frozen skill contracts** — `infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`
  freezes 8 infra skills by content hash. Editing a frozen SKILL.md body requires Owner
  approval + re-freeze per the canonical algorithm documented in that contract's header
  (reproduce the old hash first to prove the algorithm, then record the new hash and bump
  `frozen_at`).

## Verification (either tool, from repo root)

```bash
uv run python scripts/sdd/check_capability_schema.py --all
uv run python scripts/sdd/check_traceability.py --all
uv run python scripts/sdd/check_contracts.py --all
uv run python scripts/sdd/generate_index.py   # after adding/removing a capability
```

## See also

- Root `AGENTS.md` (roster + self-enforced boundaries) · `capabilities/CLAUDE.md`
  (Claude-specific working notes, same layer)
- `sdd/constitution.md` · `sdd/lifecycle.md` · `sdd/gates.md` · `sdd/workflows/` (task routing)
- `policies/ai-agent.md` §4 (canonical 10-enum) + §7 (pre-flight verification discipline)
