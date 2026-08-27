# Reviewer packet — `tranche-2-flow-build`

> Epic #499 PR-C0 · plan §2.7 item 9 / §2.8.5 · candidate commit `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`

## 0. What you are being asked to judge

1. **Trigger judgment (mandatory, per capability)** — does the rendered `codex_discovery_summary` preserve the *triggering semantics* of the source `description`? It must not widen the trigger (Codex firing the skill where Claude would not) nor narrow it (the skill becoming undiscoverable).
2. **Body fidelity spot-check (sampled, not exhaustive)** — §2.7 asks for `抽查`, explicitly *not* an unaided full-text read. The coverage report already proves structural closure; your sample is about meaning.
3. **Verdict** — `approved` or `rejected`. There is no pending value: if you have not actually performed the judgment, do not record one.

The author of this packet may not fill in your verdict. The digests in §2 *were* computed by the author's producer — so before copying them into your record, recompute them yourself with the command in §3 and confirm they are the values your review was actually performed against. The producer will refuse to emit an index whose record disagrees with the tree, but it cannot tell whether a record is genuinely yours; that part rests on you creating it.

## 1. Trigger judgment material

### `mj-agent-flow-implement`

**Claude-side source `description`** (1521 chars)

```text
This skill orchestrates mj-agent coding methodology (HITL Stage 8 Implementation) — applies red-green-refactor for behavior changes, root-cause-first for bug fixes, fresh-evidence verification before claiming completion, and **mj-agent-specific 3-flavor classification** (A pure code / B in-source canonical 永远 HITL / C infra) per HITL_Prompt §4.7. Make sure to use this skill whenever the user says "开始编码", "开始实现", "implement", "实现 SPEC", "implement plan", "Stage 8 编码", "TDD", "test first", "red-green", "先写测试", "复现 bug", "root cause", "排查 bug", "debug", "声称完成前", "实现完成验证", "fresh evidence", "before claiming done", or after Plan/SPEC has been confirmed and the user is ready to write code in mj-agent. Direction-distinct from mj-agent-flow-verify (Stage 10 command matrix), mj-agent-flow-self-review (Stage 11 11-item checklist), and mj-agent-flow-scope-drift (Stage 9 diff vs Plan) — this skill handles **coding-process methodology**. Outputs step-by-step coding plan + Rules 1-15 enforcement; can sub-call superpowers:* skills as optional methodology enhancers. Does NOT execute commands — that's Stage 10 by mj-agent-flow-verify. **B 风味 in-source canonical 改动**（src/mj_agent/{skills,prompts}/）**永远触发 §3.1 必停 HITL**，建议先用 mj-agent-runtime-{skill-doc-improve, prompt-version-bump}（PR-C2）propose diff。Do not use for: GitHub Issue creation, branch creation, commit, push, PR creation (use respective git family skills), or B-flavor in-source canonical edit (use mj-agent-runtime-* skills in PR-C2 to propose diff first).
```

**Codex-side rendered `codex_discovery_summary`** (277 chars, budget 1024)

```text
Stage 8 coding methodology: red-green-refactor TDD, root-cause-first bugfixing, fresh-evidence completion checks and 3-flavor change classification; use when asked to 开始编码, implement a confirmed plan or spec; in-source canonical (B-flavor) edits always stop for Owner approval.
```

Coverage: **46 items** — dependency-route 3, frontmatter-description 1, heading 17, level-handler 4, owner-stop 8, prohibition 13.

- **39** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **6** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `owner-stop-001` | owner-stop | `T2a` | `body-line:30` |
| `level-handler-001` | level-handler | `T2a` | `body-line:40` |
| `level-handler-003` | level-handler | `T2a` | `body-line:228` |
| `dependency-route-001` | dependency-route | `T2b` | `edge:edge-flow-implement-flow-diagnose` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-implement-flow-verify` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-implement-runtime-wildcard` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `6aff6a74af4cc1b43d8db6c944ba4d9ca6e13e232ccb0355d0aae1e345aed629`
- candidate artifact `0b38eb853c966cc2dcdda13f2cddb75b50aa5497bccb447be0c15b695c70af71`
- coverage report [`mj-agent-flow-implement.json`](../coverage/mj-agent-flow-implement.json) — `inventory_sha256` `e225683ba572d9478c0ca772fd9dc665b2ea916d77a28d0721791cd5e916405e`

### `mj-agent-flow-verify`

**Claude-side source `description`** (1180 chars)

```text
This skill orchestrates mj-agent local verification (HITL Stage 10) — auto-runs Level A read-only checks (ruff / mypy / hardened offline pytest unit+eval / compileall / wikilinks / frontmatter / git status), verifies structured skips for pytest external bands, and HITL-confirms explicit Level B probes (mj-agent check / langgraph dev Studio probe / docker compose up) based on detected change scope (mj-agent 7 modules / docs / .claude/skills/ / infra). Make sure to use this skill whenever the user asks "本地验证", "测试编排", "local verification", "跑测试", "回归", "verify changes", "本地跑一遍", "检查改动", "before commit run tests", "Level A", "Level B", "offline pytest runner", "Studio 探针" in the mj-agent context. Outputs a Verify Report aligned with execution-loop §5 双 Level matrix; does NOT auto-run Level C destructive operations (compose down -v / 拆 storage volume / production-touching commands). Do not use for: pre-commit dual-section + 11-item checklist (use mj-agent-flow-self-review, Stage 11), Stage 9 scope drift (use mj-agent-flow-scope-drift), Stage 8 coding methodology (use mj-agent-flow-implement), or PR-level review responses (use mj-agent-flow-review-respond, Stage 13).
```

**Codex-side rendered `codex_discovery_summary`** (258 chars, budget 1024)

```text
Stage 10 local verification: run the read-only check matrix (lint, types, offline tests, doc validators) and gate side-effect probes behind explicit confirmation; use for 本地验证, local verification, 跑测试 before commit; destructive operations are never auto-run.
```

Coverage: **88 items** — dependency-route 1, frontmatter-description 1, heading 19, level-handler 34, owner-stop 1, prohibition 14, validator 18.

- **81** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **5** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **1** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-verify-flow-self-review` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `1d8fe73fb177ee631d67230b96a66a120dc29be1c259464f164652e70682d174`
- candidate artifact `0bc413e1b5480b802042824a73f5bb8f1c5f47727844b9ccac7046e69862a4f0`
- coverage report [`mj-agent-flow-verify.json`](../coverage/mj-agent-flow-verify.json) — `inventory_sha256` `5d1b5443aa2435f6eda82ddc2ce3cb4015455ba97ceba3e5a9d30a4cf6d3a118`

### `mj-agent-flow-self-review`

**Claude-side source `description`** (1236 chars)

```text
This skill performs mj-agent AI self-review (HITL Stage 11) before commit — verifies the staged diff matches the linked Plan / SPEC, runs scope-drift sub-call, and produces the execution-loop §6 (实操矩阵见 §5) dual-section report (本地验证 / AI 自检) plus a 12-item mj-agent-tuned checklist (kernel execution-loop §6 is an 11-item list; these 12 are the mj-agent-specific tuning) plus a commit message draft via mj-agent-git-commit. Make sure to use this skill whenever the user says "AI 自检", "self review", "commit 前检查", "diff 自审", "本地验证后", "提交前自查", "pre-commit review", "Stage 11", "11-item checklist", "12-item checklist", or after running tests / lint / typecheck and before `git commit` in the mj-agent context. Includes mj-agent-specific 5a/5b/5c/5d reverse scan extending to src/mj_agent/{skills,prompts}/ + qcm_catalog.yaml. Outputs go/no-go recommendation with HITL questions for medium/high risk; does NOT auto-commit. Do not use for: Stage 9 scope drift detection only (use mj-agent-flow-scope-drift, sub-called here), Stage 10 command matrix execution (use mj-agent-flow-verify), Stage 13 review response on others' comments (use mj-agent-flow-review-respond), or commit message format only (use mj-agent-git-commit, sub-called here).
```

**Codex-side rendered `codex_discovery_summary`** (246 chars, budget 1024)

```text
Stage 11 pre-commit self-review: verify the staged diff against the plan, run the scope-drift sub-check and the 12-item checklist, and draft the commit message; use for AI 自检, self review, commit 前检查; outputs go/no-go and never commits by itself.
```

Coverage: **50 items** — dependency-route 3, frontmatter-description 1, heading 23, owner-stop 1, prohibition 15, validator 7.

- **46** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **0** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **3** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-self-review-flow-scope-drift` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-self-review-git-commit` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-self-review-git-push` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `1864c528a4483ba5bdae363088da393a24874bd8e872755f0084bab54714cf93`
- candidate artifact `b26b54a4a8bea1ffefb56a3282cf49600deb72a25fb60140f46b4e42c21cead2`
- coverage report [`mj-agent-flow-self-review.json`](../coverage/mj-agent-flow-self-review.json) — `inventory_sha256` `e8e4e01b9faa5887155bd58b6de7d887b9ac8d33e264ad0fd46e518ddf6822ad`

## 2. Digests to copy into your record

| field | value |
|---|---|
| `reviewed_candidate_commit_sha` | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f` |
| `reviewed_source_set_sha256` | `f2a4ef57bae4bf4818bda8ce94d0f79635cdab266f55e0da4f510517dece92e3` |
| `reviewed_artifact_set_sha256` | `363a1bfb7e0e3554438980ca5f744b6e45c4917f939725cd004699996a550a23` |

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
cap = 'mj-agent-flow-implement'
with tempfile.TemporaryDirectory() as t:
    r = b.render_candidates(pathlib.Path('.'), '36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f', pathlib.Path(t))
    print(r.outputs[f'.agents/skills/{cap}/SKILL.md'].decode('utf-8'))
EOF
```

Do **not** run the probe's `emit-fixtures` mode for this: it writes into `evidence/development-agent-v8/probe/fixtures/` — a tracked artifact PR-P1b froze — and it emits digests, not carrier text.
