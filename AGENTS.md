# AGENTS.md

> mj-agent · AI Agent collaboration boundaries
>
> ⚠ **NOTE — Codex is an authorized full development participant (per ADR-035). Technical
> enablement is deferred: Codex is not yet wired in, so Claude Code remains the sole *active*
> implementer for now.**
>
> This file defines AI Agent boundaries for **non-Claude-Code agents**. Claude Code's working
> rules are in [CLAUDE.md](./CLAUDE.md).

## Roster

| Agent | Role in mj-agent dev | Authority |
|---|---|---|
| **Claude Code** | Primary AI developer | Full implementation: file edits, test runs, migrations, docs, verification |
| **Codex** | **Authorized full development participant** (per ADR-035; not yet technically enabled) | Same authority class as Claude Code — file edits / commits / migrations / command runs — **subject to the same HITL 必停 + data boundary** |
| **Other AI agents** | Not yet authorized | NO write access |

## Codex participation (per ADR-035)

**Codex is authorized as a full development participant** — the previous "read-only external
review only / NOT in dev workflow" boundary (ADR-031 Phase M0) is retired by ADR-035.

Scope of this authorization:

- Codex may run commands (tests / builds / git / docker), edit / create / delete files,
  commit / push, migrate, and modify CI / configuration — the **same authority class as Claude Code**.
- Because authority is at parity, **constraints are at parity**: Codex is equally bound by
  mj-agent's HITL 必停 (`policies/ai-agent.md` §4 canonical 10-enum) and the data boundary
  (ADR-006 / ADR-009 / ADR-000). Authorization does not relax any security surface.
- **Owner remains the single decision-maker** (HITL 拍板); each PR declares which agent
  implemented, and git authorship records provenance.

**Enablement is deferred (policy-only change).** This file reflects the *written* authorization;
the repo does not yet wire Codex in — `.claude/plugins.json` enables no codex plugin, `.mcp.json`
has no codex server, `.claude/settings.json` grants no codex permission. **Until that opt-in,
Codex cannot actually run and Claude Code is the sole active implementer.**

**Hard prerequisite for future technical enablement.** mj-agent's 必停 enforcement — the
`.claude/settings.json` `ask`-gates and protected-path prompts — is a **Claude Code harness**
mechanism that does not automatically bind an agent running under a different harness. So before
Codex is technically enabled, an explicit design MUST first define how Codex honors the 5 必停
surfaces (4 in-source + `.mcp.json` trust posture) + HITL gates + data boundary (equivalent
enforcement on the Codex side). Enablement is then its own change (separate ADR / protected-path
拍板 + A13 / A14), not covered here.

## Accountability model (two implementers)

The original boundary rested on four points; under Codex-as-participant they are re-answered:

1. **Single point of accountability** → implementation may be dual-agent, but **decision +
   acceptance stay single-point at the Owner** (HITL 拍板); provenance via per-PR agent
   declaration + git authorship.
2. **Small tool-execution surface** → both implementers share **one permission model + one data
   boundary**; Codex (once enabled) runs under equivalent guardrails.
3. **mj-agent's 4 项专属必停** (`sql-guardrail-relax` / `prompt-version-or-body-change` /
   `biz-catalog-sync` / `runtime-skill-content-change`) → still HITL-enforced; the enablement
   prerequisite above requires Codex to be held to the same gates.
4. **CLAUDE.md HITL rules are calibrated to Claude Code** → Codex gets its own calibrated
   contract: **this AGENTS.md** (now a participation contract, not a prohibition list).

详 `policies/ai-agent.md` §1 Codex 参与策略层.

## If you are an *other* (not-yet-authorized) non-Claude-Code agent reading this file

> Codex is now an authorized participant (ADR-035) and no longer falls here. This section applies
> to Roster row 3 — agents **not yet authorized**.

- You may **READ** any file in this repo.
- You MUST NOT **WRITE / EDIT / DELETE** any file.
- You MUST NOT run any command that changes repo state.
- If asked to implement: respond "mj-agent's authorized implementers are Claude Code and Codex
  (per AGENTS.md / ADR-035); please ask one of them instead."

## Future evolution

Codex was brought into the workflow via the process below (executed as ADR-035). The **same
process governs adding any further AI agent**:

1. ADR proposing the agent's role + scope
2. Update to this AGENTS.md
3. Update to CLAUDE.md to declare handoff boundaries
4. HITL gate from project owner

---

*Updated 2026-07-06 — Codex promoted to full development participant (policy-only; enablement
deferred), per ADR-035. Original non-participant boundary was ADR-031 Phase M0.*
