---
type: policy
artifact: ai-agent
state: draft
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-07-06
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: AI Agent Boundaries

> Phase M0 — 4 段 native 内容 ✓（§Codex 参与 [ADR-035 起；原 §Codex 非参与] / §Subagent Split A3 / §Symbol-first Search A5 /
> §HITL Required Scenarios）.
> 其余段（§Read/Write boundary / §Read priority / §Output requirements）在 Phase M2 内容填充.

## §1 Codex 参与策略层（native；最高优先级）

**当前 mj-agent 项目授权 Codex 作为完整开发参与者（per ADR-035 + 2026-07-06 amendment）。standalone
Codex（路径 A）已开——由 `AGENTS.md`（其 operating contract）+ Codex 自身权限治理，可运行命令 + 做
开发；仅 (B) Claude Code 调用 Codex 插件这条路径的技术 wiring 延后.**

| 原则 | 含义 |
|---|---|
| 实施来源 | 文件修改、代码实现、测试运行、目录迁移、文档落地、验证总结可由 Claude Code 或 Codex 完成（Codex 使能后）；两者同属实施 agent. |
| 授权对等 → 约束对等 | Codex 与 Claude Code 同一授权类；相应**同样受** HITL 必停（§4 canonical 10-enum）+ 数据边界（ADR-006 / ADR-009 / ADR-000）约束；授权不放宽任何安全面. |
| 决策单点 | Owner 仍是唯一决策者（HITL 拍板）；实施可双 agent，决策与验收单点不变；每 PR 声明由哪个 agent 实施 + git authorship 记溯源. |
| 两类使能须区分 | **(A) standalone Codex** 由 `AGENTS.md` + Codex 自身权限治理，**已开**——Codex 在自身 harness 下跑，mj-agent `ask` 门 / protected-path prompt / L1·L1b 代码级 guardrail **不约束它** → 5 必停 + 数据边界靠 `AGENTS.md` **self-enforced prose**（Codex 自守）enforce. **(B) Claude Code 调用 Codex 插件**（`.claude/plugins.json` + `.claude/settings.json` + MCP wiring）仍延后为独立 opt-in；(B) 延后不限制 (A). |
| 边界文件 | 详 `AGENTS.md`（Roster + Codex 参与契约 + 使能前置）+ `CLAUDE.md` §Codex Status + `decisions/ADR-035`. |

**问责模型（原「非参与」四条 rationale 的重述）**：

1. **Single point of accountability** — 决策 + 验收单点在 Owner（HITL 拍板）；实施可双 agent，
   溯源靠 per-PR 声明 + git authorship.
2. **Tool execution surface 受控** — 两实施 agent 共用同一数据边界；Codex 在自身 harness 下靠
   `AGENTS.md` self-enforced prose 自守（非 mj-agent 技术门）.
3. **4 项 in-source 专属必停**（`sql-guardrail-relax` / `prompt-version-or-body-change` /
   `biz-catalog-sync` / `runtime-skill-content-change`；per §4 canonical 10-enum）仍 Owner-HITL 门；
   Codex 按 `AGENTS.md` self-enforced 边界自守（编辑前须 Owner 拍板）.
4. **CLAUDE.md HITL 规则** 按 Claude Code 读写契约校准 → Codex 用自己的校准契约（`AGENTS.md`）.

每次任务输出末尾须**声明 Codex 参与情况**（`Codex invocation: NONE` 或描述其具体贡献）；standalone
Codex 已开后该声明可为 non-NONE（描述 Codex 贡献）.

## §2 Subagent Split 准则（A3 — Anthropic 大型代码库最佳实践；native）

**强制触发条件**（满足任一即必须走 read-only explore subagent，而非 main session 直接 read）：

| 触发 | 行动 |
|---|---|
| scope 涉及 ≥ 2 capability | dispatch `Explore` subagent 输出 RepoScanResult 文件 → main session 读 RepoScanResult 编辑 |
| 预计 Read 文件 ≥ 50 个（含 `docs/` / `archive/`） | 同上 |
| 任务起点是"我需要先了解 X"（探索性问题） | 走 `mj-agent-flow-repo-scan` skill |
| Phase M5 / M6 大规模迁移 / 归档前的 stale-reference 扫描 | dispatch 2-3 parallel explore subagents 分 path-scope |

**理由**（per Anthropic 博客 "Effective context engineering for AI agents"）：split exploration
from editing — read-only subagent 输出 findings 文件，main agent 用文件全貌编辑，避免 main
session context 被探索性 read 污染.

**反例**（违反 A3）：在 main session 连续 `Read` ≥ 50 个 docs/archive/ 文件做"调研" — context
膨胀直接吞掉编辑期可用预算.

## §3 Symbol-first Search 准则（A5 — Anthropic 大型代码库最佳实践；native）

mj-agent 启用 `pyright-lsp` plugin（详 `.claude/plugins.json`）→ Python 符号查询优先 LSP，
而非 string grep.

| 场景 | 旧方式（grep） | LSP 方式 |
|---|---|---|
| 查 `make_graph` 函数 | grep `make_graph` 全仓 → 命中 docstring / 注释 / 旧 plan | LSP `find_definition` → 仅 `src/mj_agent/agent.py:NNN` |
| 查 `ALL_TOOLS` 用法 | grep `ALL_TOOLS` → 命中 `.py` + `.md` + plan | LSP `find_references` → 仅 Python 真实引用 |
| 重命名 `find_biz_context` | sed 全仓替换 → 风险高 | LSP `rename` → 精确 |

**约束（fallback）**：LSP 不替代 grep / Glob —— 当查询是 string pattern（"TODO" / 文档关键字 /
non-Python 文件）时 grep 仍是首选.

**Pyright vs mypy 差异**：mj-agent CI 用 `mypy --strict src/mj_agent`；LSP 用 pyright；二者
type inference 在 some edge case 有差异（per R-G23）. 出现差异时以 mypy 为准（CI 阻塞 source
of truth），LSP 仅作交互式辅助.

## §4 HITL Required Scenarios — Canonical 10-Enum（M3-FU-HITL-ENUM 收敛）

任何 PR 触及以下 enum 之一必须 HITL 人审（CI blocking gate 不覆盖此层；`sdd/gates.md §4`
是本 enum 的 in-source 子集，前 4 行）：

| Enum | Surface anchor | Notes |
|---|---|---|
| `sql-guardrail-relax` | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | 4 层 SQL 防御核心；`sdd/workflows/cross-capability-change.md` |
| `runtime-skill-content-change` | `src/mj_agent/skills/*/SKILL.md` body | per `runtime-skill.contract.yml hitl_required[]`；propose+拍板+apply via `mj-agent-runtime-skill-doc-improve` |
| `prompt-version-or-body-change` | `src/mj_agent/prompts/system.md`（version 或 body 任一） | 含义吸收原 `prompt-version-bump` + "Prompt 行为边界变更" 两 trigger |
| `biz-catalog-sync` | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | per `runtime-skill.contract.yml`；上游 mj-system QCM 同步 |
| `mcp-server-trust-posture-change` | `.mcp.json` server inventory / trust posture / credential mode | per `claude-skill.contract.yml hitl_required[]`；A14 PR gate template |
| `declared-contract-change` | `capabilities/*/contracts/*.{yml,feature}` + agent tool 列表 + agent.contract.yml | 含义吸收原 "cross-capability contract 变更" + "Agent tool 列表 + schema 变更" |
| `database-migration` | `mj_agent_memory` schema / Alembic / `docker/postgres-init/*` | mj-agent memory pg state 变更 |
| `secrets-grants-or-prod-config` | `config/secrets*.enc` / GRANT SQL / analyst role / `docker/compose.prod.yml` / 数据-LLM 边界 ADR-000 | 含义吸收原 "secrets / 权限 / GRANT" + "生产运行方式变更" + "数据-LLM 边界 ADR-000" 三 trigger |
| `ci-blocking-gate-toggle` | `.github/workflows/ci.yml` `continue-on-error` flip 或新增 blocking gate | per Stage C C-a 流程；M-FU plan 必先 register |
| `bulk-content-purge-or-migration` | ≥10 file delete/move 或 archive ceremony | 含义吸收原 "删除 / 迁移 / 归档历史内容" + "大规模目录迁移（≥10 文件）" |

补充 procedural HITL（不绑单一 surface anchor；走 PR review 流程，不入上表 canonical enum）：
- ADR `state` 变化（`draft → active` / `active → deprecated` / `supersede`）
- Phase 边界（Stage entry / closure；per Phase M2/M3 kickoff outline）

> **Post-merge tail（EVAL-backlog 自动开单）**：`runtime-skill-content-change` /
> `prompt-version-or-body-change` 触及的 PR merge 后，自动开 `[EVAL backlog]` follow-up Issue
> （A11 transitional-waiver 期兜底；无论本 PR 是否带 EVAL 引用）。规则体见
> `sdd/workflows/execution-loop.md §7.3`（HITL_Prompt §4.15 Rule 11 的 kernel home）。

> **Enforce 机制（ADR-034；拍板即落盘）**：本 enum 触发 = **AI 提议 + Owner 拍板 + AI
> 落盘**，不再要求 Owner 手动转写。前 4 项 in-source 专属必停由 `.claude/settings.json`
> `ask` 列表逐写拍板门 enforce（原 `deny` 物理硬锁已解除）；`mcp-server-trust-posture-change`
> 等 protected-path（`.mcp.json` / `.claude/**`）由 harness 强制权限 prompt enforce。两类
> 落盘后均由 **merge review（A13 settings allowlist / A14 .mcp.json trust posture）兜底**。
> **仅交互模式成立**——`auto` / `bypass` 模式下放宽类改动被 classifier 硬拦，须切交互模式
> （详 §9 + `sdd/workflows/execution-loop.md §3.0`）。

## §5 可修改路径白名单 / 必须 HITL 清单

> TBD: Phase M2 — 详 path-level 表（与 root CLAUDE.md "What Claude May Edit" / "What Claude
> Must Not Edit Without Approval" 段同步；详 `mj-agent-refactored-structure.md` §17 CLAUDE.md
> 模板 §What Claude May Edit / §What Claude Must Not Edit Without Approval）.

## §6 每次任务输出要求

> TBD: Phase M2 — 详 12 字段输出模板（详 `mj-agent-refactored-structure.md` §17 CLAUDE.md 模板
> §Output Requirements + spec-anchored-calm-lampson §11.6）.

## §7 Pre-flight Verification Discipline

> Parent rule for `M3-FU-PREFLIGHT-CI-PIPELINE-PARITY` (dep-change sub-rule
> append target; D-3f Stage D).

### Standing rule

Any claim of the form "spec X is [blocking | active | PASS | done | locked | ready]"
— applied to validator output, CI gate state, contract activation, anchor presence,
deliverable count, or `§4` canonical 10-enum trigger state — MUST be empirically
verified against the running system before any toggle, commit, anchor flip, or
downstream outline authoring that depends on the claim. **Spec brief / plan body /
commit message body is NOT ground truth; only running-system observation is.**

适用范围: 所有 AI agent 行动 (Claude Code / 任何 sub-agent / Codex 若使能),
覆盖 M-FU plan 决策 / Stage 边界 transition / `ci.yml continue-on-error` flip /
freeze anchor 解锁 / `§4` canonical 10-enum surface 修改 / declared contract amend.

### Trigger conditions (满足任一 → pre-flight verify MANDATORY)

- Toggling a CI gate `continue-on-error: true → false` — `ci-blocking-gate-toggle`
- Committing a declared contract `state` flip (`draft → active` / `active → deprecated`)
  — `declared-contract-change`
- Releasing / refreshing freeze anchor `content_hash` or `frozen_at` on any of the
  10 必停 surfaces (4 `src/mj_agent/` in-source + 6 `.claude/skills/mj-agent-infra-*`)
  — `runtime-skill-content-change` / `prompt-version-or-body-change` /
  `mcp-server-trust-posture-change`
- Closing a M-FU plan as `state: completed`
- Authoring a Stage entry / closure brief that cites prior-Stage deliverables
  (validator outputs / contract field semantics / anchor identities / canonical
  enum names / freeze surface counts)
- Marking a Stage / Phase complete (closure brief 出据)
- Any other surface modification matching `§4` Canonical 10-Enum

### Insufficient verification modes (banned shortcuts)

- "Spec brief / plan summary / commit message body says X" — 文本断言 ≠ running-system fact
- "Validator `--dry-run` exited 0" — dry-run 仅校验 invocation surface, 不跑 validation logic
- "Sample N of total claimed PASS" with N < 3 AND N < 10% of population — 部分 sample
  不足排除 cluster failure
- "Latest CI overall PASS" without per-gate outcome inspection — `continue-on-error: true`
  下 gate fail 不显, 与真 PASS 不可区分
- 从 git commit message 推断 working tree 状态 (commit body 说 "X registered" → working
  tree 仍可能缺失)
- 凭 ≥ 1 Stage 前 memory 推断 validator 行为 — Stage 间 SUT 变化频繁, 旧 memory 不可信

### Sufficient verification modes (required depth)

- **Read validator source** 确认实际 check claimed property (不是 stub / skeleton /
  placeholder return-0)
- **Run validator against real data** (not synthetic fixture; not empty input) —
  capture stdout/stderr verbatim
- **Inspect output reflects actual validation** (count matches expected; errors
  surface as expected; PASS messages explicit)
- For "deliverable present" claims: **glob-list files** + verify count + names +
  `body_sha256` if anchor-locked
- For "spec says X" claims: **read spec section text verbatim**, not summary
- For cross-Stage claims: **diff against prior-Stage baseline** (git log +
  content_hash snapshot), not in-flight working tree
- For canonical enum / surface anchor claims: **read `§4` verbatim post-latest-commit**,
  不凭 memory

### Failure-mode cluster (实证锚定)

以下案例 — 均为 Phase M2 closeout / M3 pre-flight transition 期 spec brief vs reality
不一致的 intercept 实例 — 是本 discipline 的实证基础. Stage D 自 `4a59dc5` (D-1a §7
land) 起约 1 天内 §7 standing rule 累积 6 次 runtime application, 覆盖 5 类不同 spec
drift axes (file pre-existence / path placement / namespace collision / source provenance
/ outline-vs-actual scope); empirical validation of rule generality 超出 original Phase
M2 4-incident anchor.

#### Subsection A: Historical Phase M2 closeout intercepts (3 documented + 1 historical placeholder)

1. **V4 false-claim intercept** — spec brief 称 V4 已 "34/34 markdown-body-only PASS";
   实读 validator 源 (`scripts/sdd/check_claude_skill_contracts.py`) 跑 against real
   `.claude/skills/` 发现 V4 含 spurious-WARN parser bug, 实际 PASS=28/WARN=6/FAIL=0.
   若不 pre-flight verify, 会基于 false spec 推 M3 Stage C blocking flip 致 CI 误 fail.
   见 `M3-FU-V4-VALIDATOR-INVESTIGATE` (commit `a5614c4`).

2. **G1G2G9 skeleton intercept** — spec brief 称 G1/G2/G9 已 actionable; 实测发现
   `check_capability_schema.py` / `check_traceability.py` / `generate_index.py` 仍是
   M0 skeleton placeholder, 跑 dry-run 输出为空 PASS 而非真校验. 若不 pre-flight verify,
   会 flip 假 gate 致 false-clean CI signal. 见 `M3-FU-G1G2G9-IMPL` (commit `5cd68a6`).

3. **V3 canonical-format intercept** — Stage A 写的 V3 expected bare hex; Stage B canonical
   实为 `sha256:<hex>` prefix; field `body_section_names` vs `body_section_heads` 命名 drift.
   若不 pre-flight reread Stage B canonical 当前形式, 写出的 V3 amend 会 Stage A↔B 不一致,
   freeze contract drift. 见 `M3-FU-VALIDATOR-CONTRACT-ALIGN` (commit `e6ac9e1`).

4. *(Historical placeholder — 4th historical incident referenced in M3 kickoff outline but
   lacking traceable canonical source; remains a placeholder slot for future retrieval if
   M-FU plan archeology turns up the canonical detail.)*

#### Subsection B: Stage D runtime application evidence (2026-05-21+, post-§7 land at `4a59dc5`)

5. **D-1b A2 hook artifact pre-existence intercept** (2026-05-21, commit `0d086c2`).
   Outline 假设 `.claude/hooks/stop-claude-md-improver/` 为 new (create) scope;
   pre-flight 实测发现 `on-stop.ps1` + README 已 exist 于 commit `550e46b` (Phase M0
   "A1-A6+B1 best-practices skeleton") 内. Reframe path D (spec adjust + augment) 保留
   existing draft-producer 设计 (含 R-G21 mitigation cite) 同时叠加 D-1b bypass +
   denylist defense functions.

6. **D-2a path-level placement intercept** (2026-05-21, commit `3c4e416`). Outline 写
   `src/CLAUDE.md` top-level placement; reality 是 `src/mj_agent/CLAUDE.md` package-level
   (per Anthropic guidance "CLAUDE.md at directories where AI works"). Spec self-correction:
   top-level not created.

7. **D-2b/c/d batch bulk-pre-existence intercept** (2026-05-21, commit `3c4e416`, 同 D-2a
   commit). 4 subdir CLAUDE.md (`capabilities/` + `tests/` + `docker/` + 上述
   `src/mj_agent/`) 全在 commit `550e46b` 已落. Augment only path 应用 (cross-refs +
   §Gates slim + 各自 stale-marker refresh); 无任何 overwrite.

8. **D-3a ADR NNN namespace collision intercept** (2026-05-22, commit `633225b`). Naive
   next NNN = 031 (max `docs/adr/` active +1); pre-flight scan `decisions/` INDEX 发现
   `decisions/ADR-031_Spec_Anchored_Refactor.md` 已占用. `docs/adr/` + `archive/decisions/superseded/`
   (M5-PR3b 由 `docs/archive/adr/` 平移) + `decisions/` 共享单一 NNN namespace per `decisions/INDEX.md` L23. NNN bumped to 032.

9. **D-3b source provenance ambiguity intercept** (2026-05-22, commit `23a8504`). Plan body
   标 "restore" 但 verbatim 不在 git committed bytes (trim 发生于 `24b7ea3` (M2
   content-fill) authoring Pass 1+2, pre-commit; trimmed verbatim never entered git as
   committed state). Δ-1 path: 承认 plan body lines 132-135 作 user-authored canonical
   source 等价于 git verbatim, restore 基于 plan body 短形态扩写不超 5 行 plan cap.

10. **D-3c outline-vs-standalone-plan scope drift intercept** (2026-05-22, commit `9ff0770`).
    Outline 假设 M-FU plan body inline 在 master plan, 实际是 standalone
    `plans/[PLAN]_m3_fu_rd10c_harmonize.md` (102 lines). Standalone plan §2 scope = 4 file
    (`langchain-agent` + `docker-container` + `claude-code-skill` + `runtime-skill`), 排除
    `python.md` (canonical 不可改) 与 `prompt.md` (acceptable as-is). 若按 outline 错误指令
    走会破坏 RD10C 双锚点 invariant. ε-1 path 救场.

### Sub-rule: dev-dep introduction triggers full CI pipeline pre-flight

> `M3-FU-PREFLIGHT-CI-PIPELINE-PARITY` (registered 2026-05-21 at commit `5dcb1e3`;
> resolved 2026-05-22 at this D-3f commit).

新增 dev dependency (touch `pyproject.toml [dependency-groups]` / `[tool.uv]` /
`uv.lock` / `requirements-dev.txt` 等) 时, local pre-flight 必须跑完整 CI pipeline
steps (含 `compileall` / `ruff` / `mypy` / `pytest --collect-only` / 所有 V*/G*
validator scripts `--dry-run`), 不仅跑 outline 假设被 affected 的 gate.

Rationale: Stage C C-a flip commit (`02b1cc8`) 之后 CI `compileall` step 因
`gherkin-official` 包内 `count_symbols_py2.py` (Py2-only syntax) fail; pre-flight 未跑
compileall 因不在 "被 flip 的 gate" 范围, 实际却受新 dep 影响. Sub-rule 锁定该易错类别.

**Compliance**: 任一 CI step 失败 → 立停, 不 commit 该 dep 添加, 走 reframe
(e.g. compatible dep version / skip-pattern adjustment / 排除 `.venv`). 完整 pre-flight
命令清单见 `plans/[PLAN]_m3_fu_preflight_ci_pipeline_parity.md` §3.

### Cross-references

- `§4` Canonical 10-Enum — trigger surface anchors (本节 trigger conditions 引用)
- `sdd/gates.md §4` — in-source 4 项专属必停 (canonical 10-enum subset; 前 4 行)
- `sdd/lifecycle.md §3` — state-machine HITL transition (cross-ref to §4 canonical enum)
- `M3-FU-PREFLIGHT-CI-PIPELINE-PARITY` — dep-change sub-rule (resolved at Stage D D-3f;
  see §7 Sub-rule above)

## §8 External-Info Handoff Discipline（native；ADR-034）

当某步骤需要 **AI 无法自取的外部信息**（ip / port / endpoint URL / API key / token /
secret / DB 凭证 / 远程主机状态等——含被 `.claude/settings.json` `deny` 锁掉的 `.env` /
`secrets*.enc`），AI **不得**只抛一句含糊的"请提供 X"。必须给出**具体可执行的 Owner 操作
步骤**：

1. **精确命令**：可直接复制运行的命令（PowerShell / bash / docker / curl），含占位符变量名
   （如 `<MJ_AGENT_MEMORY_USER>`），而非"自行配置"。优先复用既有脚本（`scripts/setup-env.ps1`
   / `.claude/scripts/setup-mcp-secrets.ps1` / `mj-agent check`）。
2. **env 变量名 / 落点**：明确写哪个 env key、落到 `.env` 还是 HKCU OS env、是否需重启终端 +
   Claude Code（per `config/README.md`）。
3. **失败现象 + 校验**：给出"成功长这样 / 失败长这样"的判据（如 `curl /models` 返回码、
   `grep -E '^LLM_PROVIDER='` 命中）。
4. **会话内执行提示**：交互式登录类（如 `gcloud auth login`）提示用户用 `! <command>` 前缀
   在会话内跑，输出直接进会话。

操作落点：HITL 提问的 `Owner 执行步骤` 字段（`sdd/workflows/execution-loop.md §3.3`）。
`infra-*` skill 已是此范式样板（`mj-agent-infra-env-setup` 的 Claude vs User Execution
Boundary 表 + `mj-agent-infra-llm-endpoint-probe` 的 curl 探针）。

## §9 Protected-Path 拍板 + Merge-Review 兜底（native；ADR-034）

`.claude/**`（除 `.claude/worktrees`）、`.mcp.json`、`.claude.json` 是 Claude Code **硬编码
protected paths**——它们与 `ask` 列表面统一走"AI 改、Owner 拍板、AI 落盘"，**消灭一切手动
编辑**：

- **交互模式**（`default` / `plan` / `acceptEdits`）：写 protected path 触发 **harness 强制
  权限 prompt**（`permissions.allow` 不可抑制，安全检查先于 allow 评估）——该 prompt **就是
  Owner 拍板**；批准后 AI 落盘。这是比普通文件**更强**的门（每写必拍板），非更弱。
- **合并审查兜底**：`.claude/settings.json` 改动由 **A13**（settings allowlist review）兜底；
  `.mcp.json` trust posture 由 **A14** + `mcp-server-governance/contracts/governance.contract.yml`
  `§a14_pr_gate` 兜底。
- **`auto` / `bypass` 例外（harness 固定、不可禁用）**：`auto` 模式下 protected-path 的
  privilege-escalation（放宽 `settings.json` permissions / 改 `.mcp.json` trust）被 classifier
  **硬拦**；`bypass` 模式跳过全部检查。故此类改动 **必须在交互模式执行**，不在 `auto` 模式跑。

precedence：`deny` > `ask` > `allow`（具体 path 在 `ask` 即使 `Edit` 在 `allow` 也弹）。
仍保持 `deny` 的面：`.env`（含 Read）/ `config/secrets*.enc` / `rm -rf` 类——这些不是
"拍板后让 AI 写"的对象（外部 secret 走 §8 给 Owner 步骤）。

---

> *Phase M0 — 4 段 native；§8/§9 native（ADR-034，2026-06-20）；§5/§6 余 TBD Phase M2.*
