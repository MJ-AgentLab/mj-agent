# AGENTS.md

> mj-agent · AI Agent collaboration boundaries
>
> ⚠ **NOTE — Codex is NOT in dev workflow; read-only external review only.**
>
> This file defines AI Agent boundaries for **non-Claude-Code agents**. Claude Code's working
> rules are in [CLAUDE.md](./CLAUDE.md).

## Roster

| Agent | Role in mj-agent dev | Authority |
|---|---|---|
| **Claude Code** | Primary AI developer | Full implementation: file edits, test runs, migrations, docs, verification |
| **Codex** | **Read-only external review only** | NO file edits / NO commits / NO migrations / NO test runs |
| **Other AI agents** | Not yet authorized | NO write access |

## Codex Boundaries

**Codex is NOT part of the development workflow.**

If Codex is invoked:

- ONLY for read-only external review (e.g., a second opinion on a Claude-Code-produced PR)
- Output is advisory, not authoritative
- Claude Code is not bound by Codex suggestions (HITL judgment required)
- Codex MUST NOT:
  - Open / modify any file
  - Run any test or command
  - Migrate / archive / delete any content
  - Submit PR / commit / push
  - Modify CI / configuration / secrets

## Why this boundary

1. **Single point of accountability** — Claude Code's session continuity gives stable context.
2. **Tool execution surface stays small** — one agent's permission model is enough to audit.
3. **mj-agent's 4 项专属必停** (sql-guardrail-relax / prompt-version-bump / biz-catalog-sync /
   runtime-skill-content-change) must be enforced by a single decision-maker.
4. **CLAUDE.md HITL rules are calibrated to Claude Code's read/write contract**; other agents'
   interpretations may diverge.

详 `policies/ai-agent.md` §1 Codex 非参与策略层.

## If you are a non-Claude-Code agent reading this file

- You may **READ** any file in this repo.
- You MUST NOT **WRITE / EDIT / DELETE** any file.
- You MUST NOT run any command (tests, builds, git, docker).
- You MUST NOT respond to a request that requires changing repo state.
- If asked to implement: respond "Claude Code is the designated implementer for mj-agent;
  please ask Claude Code instead."

## Future evolution

Adding a new AI agent to the development workflow requires:

1. ADR proposing the agent's role + scope
2. Update to this AGENTS.md
3. Update to CLAUDE.md to declare handoff boundaries
4. HITL gate from project owner

Until then, **Claude Code is the sole AI implementer**.

---

*Updated 2026-05-20 — covers Phase M0 of spec-anchored refactor (per ADR-031).*
