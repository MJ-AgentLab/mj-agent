# TOMBSTONE — Superseded tri-track Documentation STANDARDs

> ⚠️ **TOMBSTONE — DO NOT TREAT AS CURRENT GOVERNANCE.**
> The 4 STANDARDs in this directory
> (`[DEPRECATED]_[STANDARD]_MJ_Agent_{Documentation_Meta_Framework_v2.2,
> Code_Side_Documentation_Framework_v1.1, Agent_Side_Documentation_Framework_v1.2,
> AI_Engineering_Execution_HITL_Prompt_v1_1}.md`) are **DEPRECATED frozen
> snapshots**. They were the v2.x tri-track documentation-governance framework
> and were archived on 2026-06-04 during **M6 PR4** of the SDD Spec-Anchored
> Refactor.
>
> Do **not** read these as live policy. The doc-governance content has migrated
> to the **SDD kernel** (`policies/` + `sdd/`). For the current authority behind
> each STANDARD, follow the `replaced-by` frontmatter and the table below.

## Ceremony context

Relocated from `docs/rule/` → `archive/rule/` (git-mv) in the SDD Spec-Anchored
Refactor (**M6 PR4**, 2026-06-04). The archive unit's `archive.yml` (sibling)
declares `ai_visibility: reference`, so active documents may cite these files
for historical traceability.

Bodies are **cite-by-vintage frozen snapshots** (per ADR-011 §5.6 + ADR-019):
internal wikilinks inside the STANDARD bodies are intentionally left
un-updated and may 404 — this is expected per the archive ceremony. The
`> [!warning]` banner at the top of each file and the maintained `archive/INDEX.md`
are the forward gateways.

## Migration map — archived STANDARD → SDD kernel successor

| Archived STANDARD | Kernel home(s) |
|---|---|
| `Documentation_Meta_Framework_v2.2` | `policies/documentation` (taxonomy / track / A1-A6 / frontmatter / sync-allowlist) · `policies/archive` (triggers / path-stability / ceremony) · `sdd/lifecycle` (working-doc) · `sdd/adapters/claude-code-skill` (§3.10 / §7.7-A12 / new-dir) · `policies/ci-gates §5.1` (A13) · `policies/ai-agent §4` (A14) |
| `Code_Side_Documentation_Framework_v1.1` | `policies/documentation` (§1 docs-as-contract / §2 taxonomy / §5 A1-A6+OB / §6 frontmatter / §8 per-type body) |
| `Agent_Side_Documentation_Framework_v1.2` | `sdd/adapters/runtime-skill` · `sdd/adapters/prompt` · `sdd/adapters/contract` · `policies/documentation §5.3` (A7-A11) · `decisions/ADR-024` (EVAL spec — **still active**) |
| `AI_Engineering_Execution_HITL_Prompt_v1_1` | `sdd/workflows/execution-loop` (17-stage loop / §7 post-merge) · `policies/ai-agent §4` (HITL enum) |

## EVAL-deferral note (ADR-024)

The EVAL framework specification formerly carried in Agent_Side §4 (4 sub-kinds
outcome / trajectory / component / integration + body 八段 + frontmatter schema)
is governed by **`decisions/ADR-024_Eval_Framework_Spec.md`, which remains
ACTIVE** and is NOT archived by this ceremony. The A8 / A11 EVAL transitional
waiver continues per ADR-024 (deferred to a later phase). Cite ADR-024, not this
archived Agent_Side snapshot, for EVAL authoring.

## Not archived — STANDARDs still ACTIVE in `docs/rule/`

The following `docs/rule/` STANDARDs are **NOT** part of this archive ceremony
and remain ACTIVE in their stable paths:

- `[STANDARD]_GitHub_Markdown.md` — Markdown / YAML syntax (GFM rendering target)
- `[STANDARD]_MJ_Agent_Commit_Message_Convention.md` — commit `<type>(<scope>)` convention
