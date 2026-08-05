---
type: plan
slug: check-frontmatter-fail-open
summary: >-
  修复 scripts/check_frontmatter.py 的 fail-open 覆盖面缺陷 —— 该 gate 以「有 frontmatter」
  定义「是 canonical」，导致缺失 frontmatter 的文档静默退出 gate 范围而非报错；改为
  SCAN_ROOTS 下所有 .md 一律要求 frontmatter、SKIP_PATH_PARTS 承载显式例外，
  并补齐该脚本此前完全缺失的单元测试（含关键负向测试）。消费者 = issue #429
owner: ranzuozhou
created: 2026-08-05
updated: 2026-08-05
state: active
version: 1.0
track: engineering-workflow
---

# [PLAN] `check_frontmatter.py` fail-open 覆盖面修复

> Issue: [#429](https://github.com/MJ-AgentLab/mj-agent/issues/429)
> 上游：[#428](https://github.com/MJ-AgentLab/mj-agent/issues/428)（`plans/` 生命周期审计）——
> 该审计撞上了本洞遮蔽的实例，但只修了实例、没修洞。
> 关联 Repo Scan：2026-08-05 对话输出（见 §2 实测事实）

## 1 缺陷

`scripts/check_frontmatter.py:150-169` 的 `find_canonical_docs()` 用
`first_chars.startswith("---")` 决定一个 `.md` 是否进候选集：

```python
if first_chars.startswith("---"):
    out.append(rel)
```

即 **「有 frontmatter」= 「是 canonical」**。这让 gate 的覆盖面由**被检查对象自己决定**：

1. 删掉某 canonical 文档的 frontmatter → 它不再进候选集 → gate **exit 0**，零告警。
2. 从未写过 frontmatter 的新文档 → 永远不被校验（#428 的 B 项即此，遮蔽 ≥3 个月）。
3. 唯一可见信号是 `OK: N canonical docs ...` 的 **N**，而**无任何机制跟踪 N** ——
   N 下降与 N 上升在输出里长得一模一样。

`validate()` 第 89-90 行的注释印证了这一意图（"caller filters those out before calling here"），
所以这不是笔误，是设计层面的 fail-open。

## 2 实测事实（2026-08-05，develop @ `1aecfc3`）

| 项 | 实测值 |
|---|---|
| SCAN_ROOTS 下 `.md` 总数（扣 `SKIP_PATH_PARTS`） | **133** |
| 其中有 frontmatter（= 当前 gate 实际覆盖面） | **133** |
| **覆盖缺口** | **0** |
| 被 `SKIP_PATH_PARTS`（`docs/_templates`）跳过 | 15 |
| 分布 | `docs` 18 / `plans` 77 / `decisions` 28 / `src/mj_agent/skills` 9 / `src/mj_agent/prompts` 1 |
| SCAN_ROOTS 下未跟踪（untracked）`.md` | 0 |
| SCAN_ROOTS 下 `README.md` | 0（仅 5 个 `INDEX.md`，均已有 frontmatter） |

> **窗口期结论**：缺口为 0 ⇒ 严格化**当下可零豁免通过**，无需先做一轮大扫除。
> 这是修此洞的最佳时机；拖延只会重新积累例外。
>
> **计数口径提示**：上表 133 是改动前 `develop@1aecfc3` 的实测值。本 PR 自身新增了这份 plan，
> 因此落地后 gate 报 **134** —— 两个数字一致，差值就是本文件。

**同类第二例（实施中发现）**：UTF-8 BOM 开头的文件同样被旧判据静默跳过 ——
`"﻿---"` 不满足 `startswith("---")`，于是一份 frontmatter **完全合法**的文档也会
整份退出 gate。严格化后它被捕获；本 PR 额外给它一条**具名**诊断（"begins with a UTF-8 BOM"）
而非笼统报「缺 frontmatter」，免得排障者对着一份肉眼可见有 frontmatter 的文件发懵。

`find_canonical_docs()` 除 `main()` 外**无其他调用方**（全仓 grep 实测），语义变更无外溢。

## 3 Scope

- **In-scope**：
  - `scripts/check_frontmatter.py`：覆盖面判据由「有 frontmatter」改为「SCAN_ROOTS 下所有
    `.md`」；缺失/空 frontmatter 成为一条**具名 violation** 而非静默跳过。
  - 同文件按 `check_ai_context_audit.py` 既有先例拆出 `find_scanned_docs()` / `check()` /
    `run(repo_root)` / `main()` 四层，使 `repo_root` 可注入（`tests/AGENTS.md` 明载：
    "Scripts under test take an injectable repo root ... so fixtures run against `tmp_path`,
    not the live tree"）。
  - 新增 `tests/unit/test_check_frontmatter.py`（该脚本此前**零测试覆盖**）。
  - 同步该文件的 module docstring 与 `validate()` 注释（二者当前都明文陈述旧的跳过语义）。
- **Out-of-scope**：
  - **不动** `.github/workflows/ci.yml` —— 本 gate 已是 blocking（无 `continue-on-error`），
    本 PR 不改任何 posture ⇒ **不触发 `ci-blocking-gate-toggle`**。
  - **不**扩展 `SCAN_ROOTS`（`evidence/` 仍由 `check_ai_context_audit.py` 单独把守）。
  - **不**新增/修改任何文档的 frontmatter（缺口为 0，无需扫除）。
  - 修法 (b)「数量护栏 / 落盘基线断言」**不实施** —— 见 §5 决策 D2。

## 4 Task Breakdown

1. **测试先行**（TDD，per `sdd/adapters/bdd-tdd.md`）：写 `tests/unit/test_check_frontmatter.py`，
   其中 AC-2 负向测试须在当前实现下**红**（证明它确实捕获此洞）。
2. 重构 `scripts/check_frontmatter.py`：`find_canonical_docs` → `find_scanned_docs`（去掉
   frontmatter 前置条件）+ 抽出 `check(repo_root)` / `run(repo_root)`；`main()` 变薄。
3. 在 `check()` 中对空 metadata 短路成单条具名 violation（避免退化成 7 条 "missing required
   field" 噪声）。
4. 刷新 module docstring 第 26 行 + `validate()` 第 89-90 行注释。
5. 跑全量 Level A 验证 + 真实树 pin。

## 5 关键决策

- **D1 — 取修法 (a) 严格化**（issue 倾向案）：SCAN_ROOTS 下所有 `.md` 一律要求 frontmatter，
  合法例外由 `SKIP_PATH_PARTS` **显式**承载。理由：把「谁该被检查」的决定权从被检查对象
  手里收回到白纸黑字的常量里，这正是 fail-open 的根治点。
- **D2 — 不实施修法 (b)（数量护栏）**：(a) 落地后 AC-3「报告数 == SCAN_ROOTS 下 `.md` 总数」
  按构造恒真，(b) 的期望值基线退化为需随每次增删文档手工维护的冗余断言，**净负收益**。
  issue 原文也只把 (b) 列为「可作为 (a) 的补充，但单独用治标不治本」。
- **D3 — 沿用 `rglob` 全量枚举，不改为只扫 git-tracked 文件**：代价是本地工作树里的临时
  `.md` 草稿会让 gate 变红。可接受 —— 仓约定本就把草稿放到仓外 vault
  （`D:/Document/My-Local-Vault/`），且实测 SCAN_ROOTS 下 untracked `.md` = 0；
  引入 git 依赖反而会让纯文件系统脚本多一个失败模式。
- **D4 — 空 frontmatter 与无 frontmatter 合并为同一条 violation**：二者在 `frontmatter.load()`
  下都得到空 metadata，且治理含义相同（该文档没有可校验的 frontmatter）。

## 6 Risk Control

- **Risk level**：**Low**
- 风险与缓解：
  | 风险 | 缓解 |
  |---|---|
  | 严格化后对未普查文件 fail-closed，CI 变红 | §2 已实测缺口 = 0；并在一次性 worktree 内跑真实树验证后才提交 |
  | 语义变更外溢到其他脚本 | 实测 `find_canonical_docs()` 无外部调用方；重命名反而让残留引用显性报错 |
  | 未来合法的无-frontmatter 文档被误杀 | violation 文案直接给出出路：补 frontmatter **或** 加 `SKIP_PATH_PARTS` 显式例外 |
  | 测试跑错工作树导致假绿 | 真实树 pin 用 `Path(__file__).resolve().parents[2]`，并在验证时打印实际 `REPO_ROOT` 自证 |
- **HITL gates**：本 Plan 仅触发 **Stage 12/13 提交与推送拍板**（commit / push / PR 由 Owner
  拍板）。**不**触发 §3.1 mj-agent 专属 4 项必停，**不**触发 `ci-blocking-gate-toggle`
  （不改 `continue-on-error`），**不**触发 `declared-contract-change`。

## 7 Verification

- **Level A 必跑**（全部在本 worktree 内）：
  ```bash
  uv run ruff check
  uv run mypy src/mj_agent
  uv run pytest tests/unit -q
  python scripts/check_frontmatter.py
  python scripts/check_wikilinks.py
  python scripts/check_ai_context_audit.py
  ```
- **Level B**：不涉及（无 DB / LLM / 容器依赖）。
- **Acceptance Criteria**（对齐 issue #429）：
  - [x] **AC-1 正向**：`python scripts/check_frontmatter.py` 在干净树上 exit 0。
  - [x] **AC-2 负向（关键）**：某文档 frontmatter 被删 → gate **非零退出**并在输出中**点名**
        该文件；恢复后 exit 0。当前实现此步会**错误地** exit 0。以 `tmp_path` fixture 承载，
        **不**污染真实工作树。
  - [x] **AC-3 覆盖面**：脚本报告的文档数 == 「SCAN_ROOTS 下扣除 `SKIP_PATH_PARTS` 的 `.md`
        总数」，且该总数由测试内**独立第二口径**枚举得出（不复用被测函数的返回值）。
  - [x] **AC-4 回归**：`uv run pytest tests/unit` 全绿 + `uv run ruff check` +
        `uv run mypy src/mj_agent` 通过。

## 8 关联

- Issue [#429](https://github.com/MJ-AgentLab/mj-agent/issues/429)（本体）·
  [#428](https://github.com/MJ-AgentLab/mj-agent/issues/428)（发现路径）
- [[../sdd/workflows/execution-loop|execution-loop]] §1 Stage 4 · [[../policies/documentation|policies/documentation]] §A2（本 gate 背书的 schema）
- [[../policies/ci-gates|policies/ci-gates]] §4（gate posture 纪律；本 PR 不动 posture）
- 先例：`scripts/check_ai_context_audit.py`（`find_entries` / `check` / `run` 分层 +
  `tests/unit/test_check_ai_context_audit.py` 的 tmp_path + 真实树 pin 组合）
