# Reviewer packet — `tranche-4-doc-git`

> Epic #499 PR-C0 · plan §2.7 item 9 / §2.8.5 · candidate commit `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`

## 0. What you are being asked to judge

1. **Trigger judgment (mandatory, per capability)** — does the rendered `codex_discovery_summary` preserve the *triggering semantics* of the source `description`? It must not widen the trigger (Codex firing the skill where Claude would not) nor narrow it (the skill becoming undiscoverable).
2. **Body fidelity spot-check (sampled, not exhaustive)** — §2.7 asks for `抽查`, explicitly *not* an unaided full-text read. The coverage report already proves structural closure; your sample is about meaning.
3. **Verdict** — `approved` or `rejected`. There is no pending value: if you have not actually performed the judgment, do not record one.

The author of this packet may not fill in your verdict. The digests in §2 *were* computed by the author's producer — so before copying them into your record, recompute them yourself with the command in §3 and confirm they are the values your review was actually performed against. The producer will refuse to emit an index whose record disagrees with the tree, but it cannot tell whether a record is genuinely yours; that part rests on you creating it.

## 1. Trigger judgment material

### `mj-agent-doc-validate`

**Claude-side source `description`** (1143 chars)

```text
This skill validates mj-agent documentation against Meta v2.2 + Code_Side v1.1 + Agent_Side v1.1 (A1-A6 schema/existence checks + A7-A11 agent-track + A12-A14 engineering-workflow + OB1-OB5 format checks) by wrapping `scripts/check_wikilinks.py` (A4 wikilinks) + `scripts/check_frontmatter.py` (A2/A3 schema + 4-value TRACK_VALUES enum). Returns PASS/FAIL/WARN/SKIP per check. Recognizes project-root markdown 5 件 (README/CONTRIBUTING/CHANGELOG/GLOSSARY/CLAUDE.md) as exempt from A1-A3 per Meta v2.2 §2.6; emits SKIP for those checks. Make sure to use this skill whenever the user says "验证文档", "检查文档格式", "文档合规审计", "文档质量检查", "check docs", "validate documentation", "audit docs compliance", "lint markdown", "wikilinks check", "frontmatter check", "Stage 11 self-review docs gate" in the mj-agent context. Direction-distinct from mj-agent-flow-verify (Stage 10 multi-domain command matrix; calls scripts directly). Do not use for: writing or modifying a document (use mj-agent-doc-author), Stage 10 verification command matrix (use mj-agent-flow-verify which sub-calls this skill's scripts), or full Plan body authoring (use mj-agent-flow-plan).
```

**Codex-side rendered `codex_discovery_summary`** (270 chars, budget 1024)

```text
Validate mj-agent documentation compliance (A1-A14 + OB1-OB5 wikilink/frontmatter checks) and report per-check PASS/FAIL/WARN/SKIP; use when asked to validate documentation, 检查文档格式, check docs, 文档合规审计; not for authoring documents and not for the Stage 10 command matrix.
```

Coverage: **47 items** — dependency-route 2, frontmatter-description 1, heading 19, level-handler 2, prohibition 10, validator 13.

- **42** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **2** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **2** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-doc-validate-doc-author` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-doc-validate-git-commit` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `b6ff6c3a15b21381312a36d76d8bd1a98a352a8f3c27ba70c292a73488c767f2`
- candidate artifact `4ca7c4c80b9e82bcde73718ede6880d5fe504a5858a4fb48545da228c9fe46f6`
- coverage report [`mj-agent-doc-validate.json`](../coverage/mj-agent-doc-validate.json) — `inventory_sha256` `94f3e732195a69afd61d24ae7f9405ed1a1cd559f57d8e55e4882c3b7aeafbd1`

### `mj-agent-git-branch`

**Claude-side source `description`** (791 chars)

```text
This skill should be used when the user asks to create a branch, name a branch, set up a Git Worktree, start feature/bugfix/documentation/maintain/hotfix work, or choose the correct branch type in mj-agent. Make sure to use this skill whenever the user says "创建分支", "新建分支", "开新分支", "create branch", "new branch", "branch naming", "worktree add", "哪种分支类型", "which branch type", "开始开发", "start feature", "start bugfix", "start hotfix" in the mj-agent context. Generates the worktree-add command for mj-agent's bare repo + 5-branch-type model. Do not use for: GitHub Issue creation (use mj-agent-git-issue), commit (use mj-agent-git-commit), push (use mj-agent-git-push), branch deletion (use mj-agent-git-delete in PR-B3+), or hotfix→develop sync after merge (use mj-agent-git-sync in PR-B3+).
```

**Codex-side rendered `codex_discovery_summary`** (258 chars, budget 1024)

```text
Create branches for the bare-repo worktree model: pick the branch type (feature/bugfix/documentation/maintain/hotfix) and generate the worktree add command; use for 创建分支, create branch, starting new work; branches are never created in-place with checkout -b.
```

Coverage: **26 items** — dependency-route 1, frontmatter-description 1, git-rule 2, heading 17, prohibition 5.

- **24** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **1** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-git-branch-git-commit` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `c75633eddbd83230025efcb505d400ecc9532af06b1dcaa402d0e50b837c2624`
- candidate artifact `bebf92d1183dafa6c31c4b54ff362710c23e9734fa1c3d36e6e31a02fba3539e`
- coverage report [`mj-agent-git-branch.json`](../coverage/mj-agent-git-branch.json) — `inventory_sha256` `72e234e0aff9081e35ac7524ef1d404ed16f7658b84ac5ed9bf854324e168260`

### `mj-agent-git-issue`

**Claude-side source `description`** (712 chars)

```text
This skill should be used when the user asks to create a GitHub Issue, draft an issue body, file a bug report, or start a new task in mj-agent. Make sure to use this skill whenever the user says "创建issue", "新建issue", "提issue", "报bug", "新任务", "开新工作", "create issue", "new issue", "report bug", "file issue", "open issue", "start new task" in the mj-agent context. Uses gh CLI with --body-file. Fills the matching .github/ISSUE_TEMPLATE/ file (8 templates, in-repo since 2026-05-20) selected by branch-type taxonomy + Intake Result. Do not use for: branch creation (use mj-agent-git-branch), commit message authoring (use mj-agent-git-commit), PR creation (use mj-agent-git-pr), or Issue triage on existing issues.
```

**Codex-side rendered `codex_discovery_summary`** (232 chars, budget 1024)

```text
Create GitHub issues from the 8 in-repo templates with branch-type routing, urgency check and full body preview; use for 创建issue, create issue, report bug, filing a new task; the create command runs only after explicit confirmation.
```

Coverage: **34 items** — dependency-route 1, frontmatter-description 1, heading 18, issue-route 4, owner-stop 1, prohibition 9.

- **32** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **1** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-git-issue-git-branch` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `20190f5ba05dd5694af3c1473468278ad1b163e0ad0de3f98be559c8a7712141`
- candidate artifact `34ce7efd8431ea79fda89a974ff2de66c26c867aa9c53e40f170a19ee6d2bd2d`
- coverage report [`mj-agent-git-issue.json`](../coverage/mj-agent-git-issue.json) — `inventory_sha256` `52fc1bf294967f511fad0c60f51a9b378a8cb09636c2c518ae88b6d32342a508`

### `mj-agent-git-pr`

**Claude-side source `description`** (879 chars)

```text
This skill should be used when the user asks to create a Pull Request, select a PR template, fill PR fields, prepare a PR body, or perform a release for mj-agent. Make sure to use this skill whenever the user says "创建PR", "新建PR", "提PR", "create PR", "pull request", "PR模板", "PR description", "发版", "release", "合并到main", "merge to main", "fill PR template" in the mj-agent context. Uses gh CLI with --body-file and the correct template per branch type. mj-agent has 5 PR templates (feature/bugfix/documentation/maintain/hotfix) plus implicit release flow. Includes dual-track A1-A10 self-check + Phase B+ A12-A14 (post v2.1 promote). Do not use for: review-respond on incoming review comments (use mj-agent-flow-review-respond in PR-B3+), merge readiness gate after CI green (use mj-agent-git-check-merge in PR-B3+), or post-merge cleanup (use mj-agent-flow-post-merge in PR-B3+).
```

**Codex-side rendered `codex_discovery_summary`** (218 chars, budget 1024)

```text
Create pull requests with the per-branch-type template, an explicit base branch and body-file discipline, including the dual-track self-check; use for 创建PR, create PR, pull request preparation; merge is never executed.
```

Coverage: **32 items** — dependency-route 1, frontmatter-description 1, git-rule 1, heading 20, level-handler 1, prohibition 5, validator 3.

- **30** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **1** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-git-pr-git-check-merge` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `bdbdcd4cf3136c8f0ba74e37a0134830b1e230fd5d137f6a49d64d6cce4496fa`
- candidate artifact `db8df09a6e927c99ecddc328eb7af0aabea16982f42ef7cbe0b5053c9d0141cf`
- coverage report [`mj-agent-git-pr.json`](../coverage/mj-agent-git-pr.json) — `inventory_sha256` `c07b22dd332ea45a2213cdfc7dff29186775fee7ebbe2a9293a55b858c4e1ecf`

## 2. Digests to copy into your record

| field | value |
|---|---|
| `reviewed_candidate_commit_sha` | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f` |
| `reviewed_source_set_sha256` | `68d44de1877061e11bb3cada597c07f66af82257f22c168a9fdda9fc3dc4d9f9` |
| `reviewed_artifact_set_sha256` | `543c67891c8246df25b35b64dd0f70b6d6720eb070e89288f8fa504b691639d7` |

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
cap = 'mj-agent-doc-validate'
with tempfile.TemporaryDirectory() as t:
    r = b.render_candidates(pathlib.Path('.'), '36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f', pathlib.Path(t))
    print(r.outputs[f'.agents/skills/{cap}/SKILL.md'].decode('utf-8'))
EOF
```

Do **not** run the probe's `emit-fixtures` mode for this: it writes into `evidence/development-agent-v8/probe/fixtures/` — a tracked artifact PR-P1b froze — and it emits digests, not carrier text.
