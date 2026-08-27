# GENERATED — do not edit anything under `.agents/`

Every file in this tree plus the repo-root `.agents.lock.json` and the generated
`.codex/config.toml` is a **generated artifact** owned 100% by
`scripts/sdd/agents_sync.py` (ADR-036 D-011/D-012/D-013/D-014; ADR-039 v2
engine). `sdd/development-agent.yml` is the whitelist SoT: every capability with
`codex_carrier: byte-copy` is projected byte-identically from
`.claude/skills/<name>/SKILL.md`, and every capability with
`codex_carrier: translated` is rendered deterministically from the same source
through the translation registry (`sdd/workflows/development-agent-workflows.yml`
+ `sdd/adapters/codex-skill-translation.yml` + the Codex preface). Codex
discovers these skills natively under `.agents/skills`; projected copies do NOT
count toward the in-tree skill SoT.

18 skills carry a Codex projection (5 byte-copy + 13 translated); 19 capabilities have no Codex carrier.

How to change a projected skill:

1. Edit the SOURCE: `.claude/skills/<name>/SKILL.md` (its own gates apply; for
   translated carriers a registry/map change additionally needs its own
   `declared-contract-change` approval).
2. Run `python scripts/sdd/agents_sync.py sync`.
3. Commit source + registry/map (if touched) + artifacts + `.agents.lock.json`
   together.

This README is itself generated, from the raw template
`sdd/adapters/codex-skills-readme.md` (its version is owned by the manifest key
`codex_readme_template_version`; the lock records the raw template SHA-256).

Never hand-edit these files — CI runs `agents_sync.py --check` (drift gates
V10/V11) and `check_agents_projection.py` (V9) against them. `--adopt <name>`
is a recovery escape hatch for byte-copy carriers ONLY (verified v2 lock CAS;
Owner HITL applies); translated carriers are never adoptable. On merge
conflicts in generated files: merge the source, re-run `sync` to overwrite the
artifacts — do not 3-way-merge artifacts.

Semantic difference declaration: the Claude Code harness `ask`-gates,
protected-path prompts and PreToolUse hooks referenced inside projected skill
bodies are NOT present under Codex. Under Codex those stop points are AGENTS.md
self-enforced duties (see the repo-root `AGENTS.md`, sections "Self-enforced
boundaries" and "Generated projections"); every translated carrier additionally
opens with the Codex preface (`sdd/adapters/codex-skill-preface.md`) declaring
the same mapping.
