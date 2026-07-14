# GENERATED — do not edit anything under `.agents/`

Every file in this tree plus the repo-root `.agents.lock.json` is a **generated
artifact** owned 100% by `scripts/sdd/agents_sync.py` (dual-agent-compat v5,
ADR-036 D-011/D-012/D-014). `.agents/skills/<name>/SKILL.md` is a byte-identical
projection of `.claude/skills/<name>/SKILL.md` for every manifest capability with
`projection: project` (`sdd/development-agent.yml` is the whitelist SoT). Codex
discovers these skills natively under `.agents/skills`; projected copies do NOT
count toward the 37-skill SoT.

How to change a projected skill:

1. Edit the SOURCE: `.claude/skills/<name>/SKILL.md` (its own gates apply).
2. Run `python scripts/sdd/agents_sync.py sync`.
3. Commit source + artifacts + `.agents.lock.json` together.

Never hand-edit these files — CI runs `agents_sync.py --check` (drift gate V10)
and `check_agents_projection.py` (V9) against them. To reverse-feed an artifact
edit into the source use `python scripts/sdd/agents_sync.py --adopt <name>`
(Owner HITL applies). On merge conflicts in generated files: merge the source,
re-run `sync` to overwrite the artifacts — do not 3-way-merge artifacts.

Semantic difference declaration: the Claude Code harness `ask`-gates, protected-path
prompts and PreToolUse hooks referenced inside projected skill bodies are NOT present
under Codex. Under Codex those stop points are AGENTS.md self-enforced duties
(see the repo-root `AGENTS.md`, sections "Self-enforced boundaries" and
"Generated projections").
