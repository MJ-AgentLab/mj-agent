# Reviewer packet — `tranche-3-flow-close`

> Epic #499 PR-C0 · plan §2.7 item 9 / §2.8.5 · candidate commit `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`

## 0. What you are being asked to judge

1. **Trigger judgment (mandatory, per capability)** — does the rendered `codex_discovery_summary` preserve the *triggering semantics* of the source `description`? It must not widen the trigger (Codex firing the skill where Claude would not) nor narrow it (the skill becoming undiscoverable).
2. **Body fidelity spot-check (sampled, not exhaustive)** — §2.7 asks for `抽查`, explicitly *not* an unaided full-text read. The coverage report already proves structural closure; your sample is about meaning.
3. **Verdict** — `approved` or `rejected`. There is no pending value: if you have not actually performed the judgment, do not record one.

The author of this packet may not fill in your verdict. The digests in §2 *were* computed by the author's producer — so before copying them into your record, recompute them yourself with the command in §3 and confirm they are the values your review was actually performed against. The producer will refuse to emit an index whose record disagrees with the tree, but it cannot tell whether a record is genuinely yours; that part rests on you creating it.

## 1. Trigger judgment material

### `mj-agent-flow-scope-drift`

**Claude-side source `description`** (1095 chars)

```text
This skill detects "scope drift" during mj-agent task implementation (HITL Stage 9) — compares the current working tree diff against the linked Plan / SPEC / Issue scope and reports per-file alignment ("in Plan §X" vs "not in Plan"). Make sure to use this skill whenever the user says "范围漂移", "scope drift", "实施超出 Plan", "diff vs SPEC", "drift check", "实施跑偏了吗", "改动还在范围内吗", "Stage 9", "scope check", "scope verification" in the mj-agent context, or before commit/push when significant code has been written. Outputs a drift report with recommendations (continue / amend Plan / split PR / pause for HITL); after Owner 拍板 applies the chosen path (e.g., amends the Plan via Edit per ADR-034); git-level actions (split PR) remain their own gates. mj-agent-specific: classifies B-flavor (in-source canonical) drift as auto-High since they always trigger §3.1 必停 HITL. Do not use for: pre-commit dual-section + 11-item checklist (use mj-agent-flow-self-review which sub-calls this skill), Stage 10 command matrix (use mj-agent-flow-verify), or Stage 8 coding methodology (use mj-agent-flow-implement).
```

**Codex-side rendered `codex_discovery_summary`** (218 chars, budget 1024)

```text
Stage 9 scope drift check: compare the working diff against the approved plan scope and report per-file alignment with continue/amend/split recommendations; use for scope drift, 范围漂移, drift check during implementation.
```

Coverage: **31 items** — dependency-route 2, frontmatter-description 1, heading 14, owner-stop 5, prohibition 9.

- **27** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **1** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **2** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-scope-drift-flow-self-review` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-scope-drift-runtime-wildcard` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `cf0ebee0681769948c2b044329d789dda08b59d7b5b6b42a8270e8af9c61f0c8`
- candidate artifact `60aa5d06738d6ee574f5fca3f8b885b342bb384973da6709fd3361c5e7219ed5`
- coverage report [`mj-agent-flow-scope-drift.json`](../coverage/mj-agent-flow-scope-drift.json) — `inventory_sha256` `807c95f82ab847b71fa4b55fe1ed67a277aa2f0b5b01e8195b3ebb2c639e35c0`

### `mj-agent-flow-review-respond`

**Claude-side source `description`** (1391 chars)

```text
This skill processes review comments and CI failures on **your own** PR (HITL Stage 15) — fetches PR reviews via gh CLI, classifies each comment (bug / suggestion / style / architecture / requirement / test / CI failure), evaluates impact on Plan/SPEC/ADR + mj-agent-specific surfaces (in-source canonical / biz_catalog / SQL guardrail), drafts modification plan + reply per comment, outputs HITL questions when comments touch requirement/API/schema/permission/user-visible-behavior or §3.1 必停 4 项. Make sure to use this skill whenever the user says "处理 review", "回应 review", "处理 PR feedback", "我的 PR 收到了 review", "review 回复", "respond to review", "comment triage", "PR comment 分类", "CI failure 分析", "Stage 15", "review respond" in the mj-agent context, or pastes a PR URL belonging to themselves with reviews to handle. Direction-distinct from mj-agent-git-review-pr (audits **others'** PRs for architecture compliance — opposite direction). Outputs per-comment classification + modification plan + reply draft + HITL flags; after Owner 拍板 auto-posts the replies to GitHub via gh / mcp__github__ (ADR-034 Q2 落盘+发帖); does NOT auto-commit or auto-modify code (those stay gated). Do not use for: reviewing someone else's PR (use mj-agent-git-review-pr in PR-B3+), pre-commit self-check (use mj-agent-flow-self-review, Stage 11), or pre-merge readiness (use mj-agent-git-check-merge in PR-B3+).
```

**Codex-side rendered `codex_discovery_summary`** (270 chars, budget 1024)

```text
Stage 15 review response on your own PR: fetch review comments, classify each (bug/suggestion/style/architecture/requirement/test), analyze CI failures, draft fixes and replies; use for 处理 review, respond to review, CI failure 分析; replies post only after Owner approval.
```

Coverage: **50 items** — dependency-route 8, frontmatter-description 1, heading 18, owner-stop 11, prohibition 11, validator 1.

- **40** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **1** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **8** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-review-respond-doc-sync` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-review-respond-flow-implement` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-review-respond-flow-scope-drift` |
| `dependency-route-004` | dependency-route | `T2a` | `edge:edge-flow-review-respond-flow-verify` |
| `dependency-route-005` | dependency-route | `T2a` | `edge:edge-flow-review-respond-git-check-merge` |
| `dependency-route-006` | dependency-route | `T2a` | `edge:edge-flow-review-respond-git-commit` |
| `dependency-route-007` | dependency-route | `T2a` | `edge:edge-flow-review-respond-git-issue` |
| `dependency-route-008` | dependency-route | `T2a` | `edge:edge-flow-review-respond-git-push` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `d91e7fc7427f68cb4e851243d32a930013e51a3186804275a1384be4e9992436`
- candidate artifact `a570008ae0eb1115a74d5c63a4a54ecb7d0992dfc8d397a7a2deec84f51cfdb3`
- coverage report [`mj-agent-flow-review-respond.json`](../coverage/mj-agent-flow-review-respond.json) — `inventory_sha256` `dea810a1f08ff904e23be3952c7e830c26aa4f3d3fa92ace550972f36f5ebef9`

### `mj-agent-flow-post-merge`

**Claude-side source `description`** (1315 chars)

```text
This skill orchestrates mj-agent post-merge cleanup (HITL Stage 17) — closes the linked Issue, updates CHANGELOG `[Unreleased]`, opens follow-up issues for deferred work + **mj-agent-specific EVAL backlog ticket auto-issue** (per execution-loop §7.3 Rule 11) when PR touches in-source canonical, **marks plan state active→completed via Edit after Owner 拍板** (per lifecycle §2.2 Rule 12; ADR-034 propose→拍板→apply), triggers branch deletion via mj-agent-git-delete + sync via mj-agent-git-sync. Make sure to use this skill whenever the user says "PR 合并后", "post-merge", "Issue 关闭", "release notes", "follow-up", "PR merged 收尾", "post-merge cleanup", "Stage 17", "EVAL backlog", "plan completed" in the mj-agent context, or right after a PR is merged. Outputs a checklist of post-merge actions; some are auto-runnable (delete branch / sync) while others are human-in-loop (CHANGELOG edits / follow-up issue creation / EVAL backlog ticket / **plan state mark** — skill proposes the active→completed diff, then Edits it after Owner 拍板). Do not use for: review response on incoming comments (use mj-agent-flow-review-respond, Stage 15), pre-merge readiness (use mj-agent-git-check-merge in PR-B3+), branch deletion alone (use mj-agent-git-delete in PR-B3+), or hotfix→develop sync alone (use mj-agent-git-sync in PR-B3+).
```

**Codex-side rendered `codex_discovery_summary`** (250 chars, budget 1024)

```text
Stage 17 post-merge cleanup: close the linked issue, update the changelog, open follow-up issues, flip the plan state after Owner approval and trigger branch deletion plus mirror sync; use right after a PR is merged, for post-merge cleanup, PR 合并后收尾.
```

Coverage: **54 items** — dependency-route 4, frontmatter-description 1, heading 27, owner-stop 2, prohibition 20.

- **49** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **4** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-post-merge-git-branch` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-post-merge-git-delete` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-post-merge-git-issue` |
| `dependency-route-004` | dependency-route | `T2a` | `edge:edge-flow-post-merge-git-sync` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `f4f6b397cc61075899c949751dcbb925564b71b5055ff8dbc13ef83b15675247`
- candidate artifact `13ab8b7d21fa796ff0e39124a14a0d1a97eba0ad460ef9e9e7e7243659669339`
- coverage report [`mj-agent-flow-post-merge.json`](../coverage/mj-agent-flow-post-merge.json) — `inventory_sha256` `0f4ff09af39bb88d812beeb0be32b029e964e0eb51d9788d542ef54880b53f64`

## 2. Digests to copy into your record

| field | value |
|---|---|
| `reviewed_candidate_commit_sha` | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f` |
| `reviewed_source_set_sha256` | `8df53f383514568729f973ab9fe42b935356e7db3d693a0de27a9850fdb99c81` |
| `reviewed_artifact_set_sha256` | `283f1cf5081fa3a340d74142b2cd3e219dea4e1d1abd7163dd6f819692370441` |

The producer refuses to emit the index unless these three values in your record equal the ones this tree computes, so a record reviewed against stale inputs cannot be silently upgraded.

## 3. Recomputing the digests yourself

This regenerates the coverage reports from Git blob bytes at the pinned commit and compares them against what is committed. It writes nothing when it agrees (exit 0) and lists the drifted reports when it does not (exit 1):

```bash
uv run --frozen --no-sync python scripts/sdd/build_fidelity_attestations.py \
    build-coverage --check --rev 36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f
```

Candidate artifact bytes are deliberately not committed (PR-P1b Gate 1 published digests only). To read the rendered text of one carrier — needed only if you want to inspect a transformed item above — render it into a scratch directory; this touches nothing tracked:

```bash
uv run --frozen --no-sync python - <<'EOF'
import tempfile, pathlib
import scripts.sdd.build_fidelity_attestations as b
cap = 'mj-agent-flow-scope-drift'
with tempfile.TemporaryDirectory() as t:
    r = b.render_candidates(pathlib.Path('.'), '36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f', pathlib.Path(t))
    print(r.outputs[f'.agents/skills/{cap}/SKILL.md'].decode('utf-8'))
EOF
```

Do **not** run the probe's `emit-fixtures` mode for this: it writes into `evidence/development-agent-v8/probe/fixtures/` — a tracked artifact PR-P1b froze — and it emits digests, not carrier text.
