---
type: policy
artifact: release
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-06-08
updated: 2026-06-08
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: Release & Semantic Versioning

> Kernel home for mj-agent's **versioning rule** (M6 X6 — absorbed from
> `docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning.md` §3-§4, which
> the kernel previously had no home for). This policy carries the **rules**;
> operational how-to (repo init, dual-push, tag commands, verification checklists)
> stays in that GUIDE, and the release **process** in
> `docs/infrastructure/cicd/[RUNBOOK]_Release_Process.md`.

## §1 Version format — `MAJOR.MINOR.PATCH`

- **MAJOR** — breaking change (API incompatible / data-boundary / SKILL·PROMPT contract incompatible)
- **MINOR** — new feature / new skill / new tool (backward-compatible)
- **PATCH** — bug fix / perf / doc fix (no API impact)

## §2 Bump rules

| Change | Version bump | Example |
|---|---|---|
| New skill / tool / subsystem | MINOR +1, PATCH → 0 | 0.1.0 → 0.2.0 |
| Bug fix / perf / doc fix | PATCH +1 | 0.1.0 → 0.1.1 |
| Data-boundary or SKILL/PROMPT contract incompatible change | MAJOR +1, rest → 0 | 0.1.0 → 1.0.0 |
| Emergency hotfix (from `main`) | PATCH +1 | 0.1.0 → 0.1.1 |

## §3 Development vs release tags

| Stage | Code version | Git tag | Branch |
|---|---|---|---|
| In development | `0.1.0` | `v0.1.0-dev` | develop |
| Release | `0.1.0` | `v0.1.0` | main (after merge) |
| Next round | `0.2.0` | — | develop (bump → new cycle) |

> Phase 0: `pyproject.toml version = "0.1.0"` tracks develop. Formal release flow
> (tags on main) activates Phase 1+.

## §4 Version-bearing files

- `pyproject.toml` `version = "..."` — **sole authority** (Phase 0).
- `README.md` / `CLAUDE.md` — optional / manual references.
- Phase 1+ may add more bearers (Dockerfile / compose / CHANGELOG); a batch-update
  script lands then (per ADR-010 §Defer). No batch script needed at Phase 0 (single bearer).

## §5 Release process

- **Phase 0**: no formal release flow.
- **Phase 1+**: the release PR uses the `release.md` template (develop → main; per
  `policies/git-branching` §4); operational steps in
  `docs/infrastructure/cicd/[RUNBOOK]_Release_Process.md`; version-management flow in
  `docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning.md` §4.

## §6 Cross-references

- `policies/git-branching` — branch types / G1·G2 / PR templates (§4)
- `docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning` — operational repo setup, dual-push (Gitee + GitHub), tag commands, verification checklists
- `docs/infrastructure/cicd/[RUNBOOK]_Release_Process` — release process runbook
- `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention` — commit `<type>(<scope>)` convention (feeds bump classification)
- ADR-010 (Git and Commit Conventions Adopted from upstream business system) — versioning adoption rationale; archived `archive/decisions/superseded/`
