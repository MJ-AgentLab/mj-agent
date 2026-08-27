# Reviewer packet — `tranche-1-flow-entry`

> Epic #499 PR-C0 · plan §2.7 item 9 / §2.8.5 · candidate commit `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`

## 0. What you are being asked to judge

1. **Trigger judgment (mandatory, per capability)** — does the rendered `codex_discovery_summary` preserve the *triggering semantics* of the source `description`? It must not widen the trigger (Codex firing the skill where Claude would not) nor narrow it (the skill becoming undiscoverable).
2. **Body fidelity spot-check (sampled, not exhaustive)** — §2.7 asks for `抽查`, explicitly *not* an unaided full-text read. The coverage report already proves structural closure; your sample is about meaning.
3. **Verdict** — `approved` or `rejected`. There is no pending value: if you have not actually performed the judgment, do not record one.

The author of this packet may not fill in your verdict. The digests in §2 *were* computed by the author's producer — so before copying them into your record, recompute them yourself with the command in §3 and confirm they are the values your review was actually performed against. The producer will refuse to emit an index whose record disagrees with the tree, but it cannot tell whether a record is genuinely yours; that part rests on you creating it.

## 1. Trigger judgment material

### `mj-agent-flow-intake`

**Claude-side source `description`** (1063 chars)

```text
This skill performs mj-agent task Intake (HITL Stage 0) — converts user requirements into a structured Intake Result with risk-level / scope / documentation needs / HITL decision points, and decides whether to write `plans/[INTAKE]_*.md`. Make sure to use this skill whenever the user says "评估任务", "intake", "Issue 创建前", "task admissibility", "需求收口", "新任务评估", "task intake", "需求评估", or asks to convert a vague description / existing plan / chat / spec into an actionable engineering task in the mj-agent repo. mj-agent-specific risk taxonomy adds 4 §3.1 必停 triggers: runtime-skill-content-change (src/mj_agent/skills/**/SKILL.md body) / prompt-version-bump (system.md version) / biz-catalog-sync (qcm_catalog.yaml) / sql-guardrail-relax (tools/sql/{guardrail,precheck}.py). Outputs Intake Result + Issue Draft + HITL Questions and stops. Do not use for: GitHub Issue creation (use mj-agent-git-issue), branch creation (use mj-agent-git-branch), repo fact-check (use mj-agent-flow-repo-scan, Stage 3), or full Plan body authoring (use mj-agent-flow-plan, Stage 4).
```

**Codex-side rendered `codex_discovery_summary`** (256 chars, budget 1024)

```text
Stage 0 task intake: convert a raw requirement into an Intake Result with risk level, scope, documentation needs and stop points; use for 评估任务, 需求评估, task intake, turning a vague description into an actionable engineering task; stops before issue creation.
```

Coverage: **57 items** — dependency-route 3, frontmatter-description 1, heading 22, issue-route 2, level-handler 2, owner-stop 14, prohibition 11, validator 2.

- **51** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **2** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **3** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-intake-flow-repo-scan` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-intake-git-branch` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-intake-git-issue` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `adb888e35cc06e93ac46f8e564b7ca8a497fc6ca10e92b165da0715572fe4773`
- candidate artifact `76c2a03ce7231bac6926b00d1958b0bfcd73ca193de8c19b041fb2456c4c4cc9`
- coverage report [`mj-agent-flow-intake.json`](../coverage/mj-agent-flow-intake.json) — `inventory_sha256` `518d6be3c00b4b579fa59224bbbcee05d631e588ef7a7e6cc7d8225df8ec5469`

### `mj-agent-flow-repo-scan`

**Claude-side source `description`** (1179 chars)

```text
This skill orchestrates mj-agent Repo Scan — the systematic fact-check of repo state against an Issue / branch / Plan before entering Plan / SPEC / Implementation (HITL Stage 3). Make sure to use this skill whenever the user has an Issue + branch and is about to write Plan / SPEC / code, or says "开始执行", "按 plan 实施", "先扫一下仓库", "repo scan", "仓库事实核查", "事实核查", "verify Plan against repo", "Plan 是否成立", "文档决策", "Documentation Decision", "反向扫描", "既有文档失真", "stale doc scan", "HITL Stage 3", "阶段 3" in the mj-agent context. Runs 8-dim scan adapted for mj-agent (no n8n; adds biz catalog drift + runtime SKILL/PROMPT reverse scan), produces §7.1 Documentation Decision matrix (10 doc types × Create/Update/None) plus Plan Verdict, and surfaces HITL questions when risk re-classifies upward. Outputs structured Repo Scan Result in conversation; does NOT modify any repo-tracked file. Do not use for: Stage 0 Intake admissibility (use mj-agent-flow-intake), Stage 4 Plan body authoring (use mj-agent-flow-plan), Stage 8 Implementation (use mj-agent-flow-implement), Stage 9 scope drift detection (PR-B3+ mj-agent-flow-scope-drift), or doc-only evaluation (use mj-agent-doc-plan in PR-B4).
```

**Codex-side rendered `codex_discovery_summary`** (250 chars, budget 1024)

```text
Stage 3 repo scan: systematic 事实核查 of repo state against the issue/plan before coding, producing the Documentation Decision matrix and a plan verdict; use for repo scan, checking whether a plan still holds, stale-doc reverse scan; strictly read-only.
```

Coverage: **53 items** — dependency-route 3, frontmatter-description 1, heading 21, level-handler 2, owner-stop 4, prohibition 12, validator 10.

- **42** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **7** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **3** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-repo-scan-doc-author` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-repo-scan-flow-plan` |
| `dependency-route-003` | dependency-route | `T2a` | `edge:edge-flow-repo-scan-git-issue` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `d1dd7c1839492b4f944bb39f17a943f1db3ad42e5c905a97cf47238aefa48f25`
- candidate artifact `ba160a28563d74965d72f6de618857fce1f3c06749e1464b52544aff3046fa55`
- coverage report [`mj-agent-flow-repo-scan.json`](../coverage/mj-agent-flow-repo-scan.json) — `inventory_sha256` `0264b62159fa14891dd95965a51c3e2627e793e632b58fab247ac7969ab57766`

### `mj-agent-flow-plan`

**Claude-side source `description`** (1155 chars)

```text
This skill orchestrates mj-agent working Plan body authoring (HITL Stage 4) — produces complete `plans/[PLAN]_*.md` content with 8 sections (linked artifacts / context / scope / 任务拆解 / 执行顺序 / 风险 / 验证 / AC / 关联), sub-calling mj-agent-doc-plan (PR-B4) for §7.1 Documentation Decision matrix and optionally mj-agent-flow-repo-scan when fact-check missing. Make sure to use this skill whenever the user says "写 plan", "写 plan body", "执行计划", "draft plan", "task breakdown", "任务拆解", "怎么推进", "Plan §X 步骤", "实施计划", "Stage 4 plan", "plan body 主体", or has Repo Scan output in hand and is ready to lay out the working plan in mj-agent. Direction-distinct from mj-agent-doc-plan which only evaluates **what documentation is needed**; this skill handles the **full Plan body**. Outputs the Plan body, then after Owner 拍板 (Stage 5 Gate 1) writes it to plans/[PLAN]_*.md directly via Write (ADR-034 propose→拍板→apply; no manual paste). Do not use for: Stage 0 Intake (use mj-agent-flow-intake), Stage 3 Repo Scan (use mj-agent-flow-repo-scan), Stage 6 SPEC/ADR/RUNBOOK authoring (use mj-agent-doc-author in PR-B4), or Stage 8 Implementation (use mj-agent-flow-implement).
```

**Codex-side rendered `codex_discovery_summary`** (259 chars, budget 1024)

```text
Stage 4 plan authoring: produce the complete working-plan body with 任务拆解, execution order, risks, verification and acceptance criteria; use when asked to 写 plan, draft plan, lay out an implementation plan; the body lands on disk only after the Owner approves.
```

Coverage: **49 items** — dependency-route 2, frontmatter-description 1, heading 16, level-handler 6, owner-stop 4, prohibition 13, validator 7.

- **45** byte-identical between source and artifact (both digests equal) — these cannot have changed meaning, provable from the tracked source alone
- **1** identical apart from leading indentation (the report digests the raw source line against the stripped artifact slice)
- **1** frontmatter description, replaced by the discovery summary — that is the §1 trigger judgment above
- **2** carry a declared transform — **this is your body spot-check surface**

| item | kind | transform | source locator |
|---|---|---|---|
| `dependency-route-001` | dependency-route | `T2a` | `edge:edge-flow-plan-doc-author` |
| `dependency-route-002` | dependency-route | `T2a` | `edge:edge-flow-plan-flow-implement` |

`T2a` / `T2b` rewrite a cross-skill reference onto the Codex carrier path or an edge-route marker; they are the only places this translation can distort a routing instruction.

- source blob `e97a79a73d74249225ec24561970911e2f273229bc3c447f71a57c8eb12172e6`
- candidate artifact `312b96da29f6e4ca83a7d22390c93817828ffc2119b6b783199ee1f4e84d471c`
- coverage report [`mj-agent-flow-plan.json`](../coverage/mj-agent-flow-plan.json) — `inventory_sha256` `a83efdfc7270c63b15e998f82b573743d59c57e610658ad2c3510149016607b2`

## 2. Digests to copy into your record

| field | value |
|---|---|
| `reviewed_candidate_commit_sha` | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f` |
| `reviewed_source_set_sha256` | `3abcc076e932fac7be3150993b1a568ff9f7a09938f2458b2ec6a51e0e4e1595` |
| `reviewed_artifact_set_sha256` | `173e45cf5c293a2795ecc56f822eec8e4218795355484605d844921ec30feacc` |

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
cap = 'mj-agent-flow-intake'
with tempfile.TemporaryDirectory() as t:
    r = b.render_candidates(pathlib.Path('.'), '36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f', pathlib.Path(t))
    print(r.outputs[f'.agents/skills/{cap}/SKILL.md'].decode('utf-8'))
EOF
```

Do **not** run the probe's `emit-fixtures` mode for this: it writes into `evidence/development-agent-v8/probe/fixtures/` — a tracked artifact PR-P1b froze — and it emits digests, not carrier text.
