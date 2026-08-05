# AGENTS.md

> mj-agent · AI Agent collaboration boundaries
>
> ⚠ **NOTE — Codex is an authorized full development participant (per ADR-035 + its 2026-07-06
> amendment). You (Codex) MAY run commands and do development work in this repo now — subject to the
> self-enforced boundaries in "Codex participation" below. This file IS your operating contract: you
> run under your own harness, so those boundaries hold only by you obeying this file, not by the
> Claude Code permission harness.**
>
> This file is the **tool-neutral collaboration contract for all AI agents** working in this repo
> (Claude Code, Codex, and any future agent). Claude Code additionally loads
> [CLAUDE.md](./CLAUDE.md) — its harness-specific working notes; both derive from the same project
> kernel (`sdd/` + `policies/` + `capabilities/`) and neither overrides it.

## Roster

| Agent | Role in mj-agent dev | Authority |
|---|---|---|
| **Claude Code** | Full-responsibility AI developer（双工具对等，no fixed primacy） | Full implementation: file edits, test runs, migrations, docs, verification — 必停 enforced by its own harness (`ask`-gates / hooks) |
| **Codex** | **Full-responsibility AI developer**（双工具对等；authorized per ADR-035） | Same authority class as Claude Code — run commands, edit / create / delete files, commit / push, migrate — **and MUST self-honor the 必停 + data boundary below** |
| **Other AI agents** | Not yet authorized | NO write access |

## Nested AGENTS.md map (same-layer local constraints)

Codex discovers `AGENTS.md` hierarchically (repo root → cwd); Claude Code sees the same files
via each sibling `CLAUDE.md`'s `@AGENTS.md` import (per dual-agent-compat plan v5 P1). Local
constraints live at:

- `capabilities/AGENTS.md` — capability catalog: contract schema obligations / frozen-contract
  surfaces / archive-reference bans
- `docker/AGENTS.md` — container security boundary: prod-compose hard stop, **Dockerfile external
  image-ref supply-chain hard stop**, `--env-file` carrier semantics, teardown safety
- `src/mj_agent/AGENTS.md` — runtime code: the 4 mj-agent-specific hard-stop surfaces + data
  boundary + loading contracts
- `tests/AGENTS.md` — test bands / fixtures / external-dependency and skip conventions

Same layering rule as this file: nested files point to the kernel, they do not restate it.

## Generated projections (`.agents/` + `.codex/config.toml`) — never hand-edit

`.agents/skills/**`, `.agents/README.md`, the repo-root `.agents.lock.json` **and the repo-level
`.codex/config.toml`** are **generated artifacts** owned 100% by `scripts/sdd/agents_sync.py`
(per ADR-036 D-011/D-012/D-013/D-014): byte-identical projections of the whitelisted
`.claude/skills/<name>/SKILL.md` sources (whitelist SoT = manifest `sdd/development-agent.yml`
`projection: project` entries), plus — since S2 (#330) — a Codex MCP config derived from
`.mcp.json` filtered by the manifest `mcp` per-server tiers (github / playwright / serena only;
`pg-mj-system-biz-*` + `ssh-manager` are PERMANENTLY excluded, ADR-006/009 data boundary) with
`codex.posture` transcribed. They are committed so Codex discovers skills under `.agents/skills`
and MCP servers via `.codex/config.toml` after `git pull`; projected copies do NOT count toward
the 37-skill SoT. Rules — they bind BOTH tools:

- **Never hand-edit** anything under `.agents/`, `.agents.lock.json`, or `.codex/config.toml`.
- Change path (skills) = edit the SOURCE skill (its own gates apply) → run
  `python scripts/sdd/agents_sync.py sync` → commit source + artifacts + lock together.
- Change path (MCP) = edit the SOURCE through its own gate — `.mcp.json` is an A14 hard-stop
  surface; the manifest `mcp` / `codex.posture` sections are protected-adjacent (D-017 Owner
  approval) — then run `sync` and commit `.codex/config.toml` + lock together. Secrets are
  referenced BY NAME only (`env_vars` whitelists; Codex sanitizes MCP child env and inherits
  the named variables) — a literal credential in this file is always a defect (G7 scans it).
- Reverse-feeding an artifact edit into the source goes ONLY through
  `python scripts/sdd/agents_sync.py --adopt <name>` (Owner HITL applies to the source write);
  there is NO adopt path for `.codex/config.toml` (fully derived).
- Merge conflict on generated files: merge the source, re-run `sync` to overwrite the artifacts —
  never 3-way-merge artifacts by hand.
- Drift gates: CI runs `agents_sync.py --check --surface skills` (**V10, BLOCKING since the P4
  flip #399, 2026-08-03**; it landed warning-first per D-016) and `agents_sync.py --check
  --surface mcp` (**V11, BLOCKING day-1 per D-016**; Owner execution record #330) plus V9
  (`check_agents_projection.py --fail-on warning`) closure / reconcile / lock / codex-config
  (PJ04x, incl. PJ044 never-tier leak) rules. **V8 / V9 / V10 are all BLOCKING as of #399** —
  one Owner `ci-blocking-gate-toggle` execution record per gate, in issue #399; eligibility per
  `plans/[PLAN]_dual-agent-compat.md` §11.2 (anchor 2026-07-14 +20d; streaks 55 / 55 / 49).
- Codex consumption semantics (spike-verified 2026-07-14, #330): project-level `.codex/config.toml`
  loads only in **trusted** projects; trust matches the exact project root or an in-repo ancestor
  entry (the bare-container entry covers all worktrees on the reference machine). Trust stays a
  per-engineer manual `~/.codex/config.toml` `[projects]` step (D-015 — no repo script may write
  it); edit that file with the Codex Desktop app closed (the app rewrites it while running).
- Semantic caveat for Codex: the Claude harness `ask`-gates / protected-path prompts / PreToolUse
  hooks referenced inside projected skill bodies are NOT present under your harness — those stop
  points are AGENTS.md self-enforced duties (see "Self-enforced boundaries" below).

## Codex participation (per ADR-035)

**Codex is authorized as a full development participant.** The previous "read-only external review
only / NOT in dev workflow" boundary (ADR-031 Phase M0) is retired. **You may run commands (tests /
builds / git / docker), edit / create / delete files, commit / push, migrate, and modify CI /
configuration — the same authority class as Claude Code.**

### Self-enforced boundaries (READ THIS — it is the only guardrail on you)

You (Codex) run under **your own** harness. mj-agent's technical 必停 enforcement —
`.claude/settings.json` `ask`-gates and protected-path prompts — is a **Claude Code harness**
mechanism and does **NOT** bind you. The **stop points themselves are tool-neutral**
(`OWNER_APPROVAL_REQUIRED`, per `policies/ai-agent.md` §4 canonical enums + dual-agent-compat plan
v5 §5.3): only the carrier differs — Claude Code stops via harness prompts, you stop by obeying
this file. Treat them as hard rules:

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
   **Also `docker/Dockerfile` external registry image refs** — `FROM <image>` and
   `COPY --from=<registry image>` (internal `COPY --from=<stage>`, e.g. `--from=builder`, is NOT in
   scope; every other Dockerfile line needs ≥ 2 reviewer, not Owner sign-off). This one is stated
   here explicitly because it binds you and **nothing else does**: it has no `permissions.ask` entry
   and no CI gate, and `docker/AGENTS.md` — where its local table lives — only loads once your cwd is
   under `docker/`. Rule body + approval levels: `policies/docker-runtime.md` §4; canonical enum
   anchor `secrets-grants-or-prod-config` (per #408 / #413).
4. **Commit / push / PR / merge — `OWNER_APPROVAL_REQUIRED` (Owner HITL 拍板).** You may prepare
   changes and run verification freely, but treat commit, push, PR creation, and merge as gated
   actions needing the Owner's go-ahead (same as Claude Code, per ADR-034).
5. **Git workflow discipline (G1/G2) binds you too.** New branches ONLY via
   `git worktree add ../<branch-name> -b <branch-name>` — never `git checkout -b` / `git switch -c`
   (G1); `gh pr create` must carry an explicit `--base` (non-hotfix → develop, hotfix → main) (G2).
   Claude Code has these enforced by a fail-closed PreToolUse hook; you self-enforce them (per
   `policies/git-branching.md`).
6. **Parity of authority = parity of constraint.** Being authorized relaxes no security surface.
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
4. **Rules live once in the project kernel** (`sdd/` + `policies/` + `capabilities/`) →
   CLAUDE.md and this AGENTS.md are per-tool **entry adapters** over that single source; this file
   is your entry point (a participation contract with self-enforced boundaries, not a second rule
   source, per dual-agent-compat plan v5).

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

*Updated 2026-07-13 — dual-agent-compat v5 P0 (#313): de-primaried wording (full-responsibility
peers), tool-neutral `OWNER_APPROVAL_REQUIRED` stop points, and G1/G2 Git workflow discipline made
explicit for self-enforcing agents.*

*Updated 2026-07-13 — dual-agent-compat v5 P1 (#320): added the nested AGENTS.md map — 4 subdir
entry adapters (`capabilities/` / `docker/` / `src/mj_agent/` / `tests/`) so both tools see the
same same-layer constraints; sibling `CLAUDE.md` files import them via `@AGENTS.md`.*

*Updated 2026-07-14 — dual-agent-compat v5 S1 (#326): added the "Generated projections" contract —
`.agents/skills/**` + `.agents.lock.json` are `agents_sync.py`-owned artifacts (first batch: 5
whitelisted skills); never hand-edit, change the source and re-run `sync`, reverse-feed only via
`--adopt` (Owner HITL). Drift gate V10 mounted warning-first.*

*Updated 2026-07-14 — dual-agent-compat v5 S2 (#330): extended the "Generated projections"
contract to `.codex/config.toml` (emitter B; 3 spikes PASS + Owner 进拍板): github / playwright /
serena(--context codex) projected from `.mcp.json` by manifest mcp tiers, secrets BY NAME via
`env_vars`, biz×5 + ssh-manager permanently excluded. MCP drift gate V11 mounted BLOCKING day-1
(D-016; ci-blocking-gate-toggle record in #330); V10 narrowed to --surface skills.*

*Updated 2026-08-03 — dual-agent-compat v5 P4 + S3 (#399): V8 / V9 / V10 flipped from warning to
**BLOCKING** (dual-axis per plan §11.2(1) — `continue-on-error: true→false` on all three, plus the
threshold axis `--fail-on error→warning` for V8 and a newly added `--fail-on warning` for V9; V10
has no threshold axis). Eligibility measured 2026-08-03: observation anchor 2026-07-14 +20 days
(gate was 07-28), consecutive-clean streaks V8/V9 = 55 and V10 = 49 (both ≥ 20), zero waiver,
ledger `evidence/ai-context-audit/2026-07_ci_audit.md`. Three separate Owner
`ci-blocking-gate-toggle` execution records in #399. V11 unchanged (already day-1 blocking).*

*Updated 2026-08-04 — docker supply-chain stop made visible to Codex (#413): self-enforced boundary
3 now names `docker/Dockerfile` external registry image refs, and the nested-map entry for
`docker/AGENTS.md` lists that hard stop. Before this, the stop existed only in `docker/AGENTS.md` —
which Codex loads only when cwd is under `docker/` — so it did not bind a root-cwd Codex session at
all. Rule body moved to the kernel (`policies/docker-runtime.md` §4); canonical anchor =
`secrets-grants-or-prod-config` (enum count unchanged at 10, per ADR-036 D-017 precedent).*
