# AGENTS.md

> mj-agent · AI Agent collaboration boundaries
>
> ⚠ **NOTE — Codex is an authorized full development participant (per ADR-035 + its 2026-07-06
> amendment). You (Codex) MAY run commands and do development work in this repo now — subject to the
> self-enforced boundaries in "Codex participation" below. This file IS your operating contract: you
> run under your own harness, so those boundaries hold only by you obeying this file, not by the
> Claude Code permission harness.**
>
> This file defines AI Agent boundaries for **non-Claude-Code agents**. Claude Code's working
> rules are in [CLAUDE.md](./CLAUDE.md).

## Roster

| Agent | Role in mj-agent dev | Authority |
|---|---|---|
| **Claude Code** | Primary AI developer | Full implementation: file edits, test runs, migrations, docs, verification |
| **Codex** | **Authorized full development participant** (per ADR-035) | Same authority class as Claude Code — run commands, edit / create / delete files, commit / push, migrate — **and MUST self-honor the 必停 + data boundary below** |
| **Other AI agents** | Not yet authorized | NO write access |

## Codex participation (per ADR-035)

**Codex is authorized as a full development participant.** The previous "read-only external review
only / NOT in dev workflow" boundary (ADR-031 Phase M0) is retired. **You may run commands (tests /
builds / git / docker), edit / create / delete files, commit / push, migrate, and modify CI /
configuration — the same authority class as Claude Code.**

### Self-enforced boundaries (READ THIS — it is the only guardrail on you)

You (Codex) run under **your own** harness. mj-agent's technical 必停 enforcement —
`.claude/settings.json` `ask`-gates and protected-path prompts — is a **Claude Code** mechanism and
does **NOT** bind you. So these boundaries hold only by **you obeying this file**. Treat them as hard
rules:

1. **Data boundary (ADR-006 / ADR-009 / ADR-000) — never bypass it.** All business-warehouse (biz)
   data access MUST go through the agent tool-chain (`find_biz_context → list_biz_tables →
   describe_biz_table → execute_sql`). Do NOT connect to any database directly (psql / psycopg / any
   client) — that bypasses the L1/L1b SQL guardrails and may use non-analyst credentials. biz access
   is **read-only** via the `analyst` role; no writes, no DDL, no schema changes.
2. **Secrets — never read or exfiltrate.** Do NOT open, print, log, or transmit `.env`,
   `config/secrets*.enc`, or any credential; do not use secrets to reach services outside the
   sanctioned tool-chain.
3. **4 项 in-source 专属必停 + protected surfaces — Owner HITL 拍板 required before editing.** Do NOT
   edit `src/mj_agent/tools/sql/{guardrail,precheck}.py`, `src/mj_agent/prompts/system.md`,
   `src/mj_agent/skills/*/SKILL.md` bodies, or `src/mj_agent/biz_catalog/qcm_catalog.yaml` without
   explicit Owner sign-off (per `policies/ai-agent.md` §4 canonical 10-enum). Same for `.mcp.json`
   trust posture, `.claude/**`, `config/secrets*.enc` / GRANT SQL, and `docker/compose.prod.yml`.
4. **Commit / push / PR / merge — Owner HITL 拍板 required.** You may prepare changes and run
   verification freely, but treat commit, push, PR creation, and merge as gated actions needing the
   Owner's go-ahead (same as Claude Code, per ADR-034).
5. **Parity of authority = parity of constraint.** Being authorized relaxes no security surface.
   When in doubt, stop and ask the Owner.

**Owner remains the single decision-maker** (HITL 拍板); each PR declares which agent implemented,
and git authorship records provenance.

### Two separate "Codex enablements" — don't confuse them

- **(A) You running here as a standalone agent** (reading this file) — governed **only** by this
  AGENTS.md + your own "Full access" permission. **This is OPEN now.** It needs no mj-agent
  `.claude/` wiring.
- **(B) Claude Code invoking Codex as a sub-tool** (the `codex:` plugin) — governed by mj-agent's
  `.claude/plugins.json` + `.claude/settings.json` + any MCP wiring. **This remains a separate,
  deferred opt-in** (per ADR-035 amendment). (B) being deferred does **NOT** limit (A).

## Accountability model (two implementers)

The original boundary rested on four points; under Codex-as-participant they are re-answered:

1. **Single point of accountability** → implementation may be dual-agent, but **decision +
   acceptance stay single-point at the Owner** (HITL 拍板); provenance via per-PR agent declaration
   + git authorship.
2. **Small tool-execution surface** → both implementers work under the same data boundary; you
   (Codex) enforce it on yourself via the self-enforced boundaries above.
3. **mj-agent's 4 项专属必停** (`sql-guardrail-relax` / `prompt-version-or-body-change` /
   `biz-catalog-sync` / `runtime-skill-content-change`) → still Owner-HITL-gated; you must not touch
   them without sign-off.
4. **CLAUDE.md HITL rules are calibrated to Claude Code** → your calibrated contract is **this
   AGENTS.md** (a participation contract with self-enforced boundaries, not a prohibition list).

详 `policies/ai-agent.md` §1 Codex 参与策略层.

## If you are an *other* (not-yet-authorized) non-Claude-Code agent reading this file

> Codex is an authorized participant (ADR-035) and no longer falls here. This section applies to
> Roster row 3 — agents **not yet authorized**.

- You may **READ** any file in this repo.
- You MUST NOT **WRITE / EDIT / DELETE** any file.
- You MUST NOT run any command that changes repo state.
- If asked to implement: respond "mj-agent's authorized implementers are Claude Code and Codex
  (per AGENTS.md / ADR-035); please ask one of them instead."

## Future evolution

Codex was brought into the workflow via the process below (executed as ADR-035). The **same process
governs adding any further AI agent**:

1. ADR proposing the agent's role + scope
2. Update to this AGENTS.md
3. Update to CLAUDE.md to declare handoff boundaries
4. HITL gate from project owner

---

*Updated 2026-07-06 — Codex is an authorized full development participant and may run commands + do
dev work now, subject to the self-enforced boundaries above (per ADR-035 + amendment). Only the
Claude-Code-invokes-Codex plugin path (B) remains deferred. Original non-participant boundary was
ADR-031 Phase M0.*
