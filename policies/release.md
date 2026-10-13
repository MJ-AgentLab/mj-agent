---
type: policy
artifact: release
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-06-08
updated: 2026-10-12
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
- `README.md` / `AGENTS.md` — optional / manual references.
- Phase 1+ may add more bearers (Dockerfile / compose / CHANGELOG); a batch-update
  script lands then (per ADR-010 §Defer). No batch script needed at Phase 0 (single bearer).

## §5 Release process

- **Phase 0**: no formal release flow.
- **Phase 1+**: the release PR uses the `release.md` template (develop → main; per
  `policies/git-branching` §4); operational steps in
  `docs/infrastructure/cicd/[RUNBOOK]_Release_Process.md`; version-management flow in
  `docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning.md` §4.

## §5.1 发布、运行验证与接受

历史release develop→main须Owner接受及独立具名发布授权，当前Agent-first日常taskPR解析器只支持主线/热修及登记任务集成关系，release需未来具名规则映射；不以现有示例或技术权限宣称已支持。

发布在具名授权、平台有效审核及必要门禁满足后由Agent执行，普通版本维护不自动要求逐内容批准。仓库批准、部署授权、实际运行验证和业务接受分记；合并/HTTP/命令成功不证明业务正确。共享环境核目标/并发，恢复按风险安排回滚PR、备份恢复、补偿或降级；尚未演练明确未验证。首期部署自动化与实际恢复演练延期，不能宣称已完成。

## §6 Cross-references

- `policies/git-branching` — branch types / G1·G2 / PR templates (§4)
- `docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning` — operational repo setup, dual-push (Gitee + GitHub), tag commands, verification checklists
- `docs/infrastructure/cicd/[RUNBOOK]_Release_Process` — release process runbook
- `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention` — commit `<type>(<scope>)` convention (feeds bump classification)
- ADR-010 (Git and Commit Conventions Adopted from upstream business system) — versioning adoption rationale; archived `archive/decisions/superseded/`
