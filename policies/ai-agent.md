---
type: policy
artifact: ai-agent
state: draft
version: 0.8
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-22
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: AI Agent Boundaries

> Phase M0 — 4 段 native 内容 ✓（§Codex 参与 [ADR-035 起；原 §Codex 非参与] / §Subagent Split A3 / §Symbol-first Search A5 /
> §HITL Required Scenarios）；§7-§9 亦 native。**§5 / §6 于 #482（2026-08-11）内容化，本文件不再有待填充节。**
> ⚠ 引用本文件请用**章节号 + 行名**，勿用行号——内容增补会整体移动行号，且无任何 gate 能发现失效的行号锚。

## §1 Codex 原生开发参与

Codex 为项目开发执行者，Owner 是决策和验收单点；实施来源由任务/PR 与 git authorship 留证。
AGENTS.md 为原生入口，政策、SDD、capability contracts 继续承载规则正文。原生资产直接维护，定向替代依据为 ADR-040。
无需旧客户端插件或投影链。对等的安全与数据约束继续适用；授权不消除保护。
每次任务报告 Codex 参与、HITL、BDD/TDD 与委派情况。

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

优先使用当前已发现的符号查询工具；未发现时采用文件搜索和 AST 等可用等价方法，不依赖个人插件。可用工具不能扩大数据或写权限。

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
| `mcp-server-trust-posture-change` | `.codex/config.toml` 服务/trust/凭据；`.codex/hooks.json`、`.codex/rules/*.rules`、原生守卫与启动器、冻结 infra 原生技能及其契约 | 原生资产直接维护；不再经 typed source/renderer/lock。所有权切换不取消 Owner 批准。 |
| `declared-contract-change` | `capabilities/*/contracts/*.{yml,feature}` + agent tool 列表 + agent.contract.yml | 含义吸收原 "cross-capability contract 变更" + "Agent tool 列表 + schema 变更" |
| `database-migration` | `mj_agent_memory` schema / Alembic / `docker/postgres-init/*` | mj-agent memory pg state 变更 |
| `secrets-grants-or-prod-config` | `config/secrets*.enc` / GRANT SQL / analyst role / `docker/compose.prod.yml` / 数据-LLM 边界 ADR-000；**#413 扩展供应链面**：`docker/Dockerfile` 外部 registry 镜像引用（`FROM <image>` + `COPY --from=<registry image>`；内部 `COPY --from=<stage>` **不**在内） | 含义吸收原 "secrets / 权限 / GRANT" + "生产运行方式变更" + "数据-LLM 边界 ADR-000" 三 trigger；供应链面规则体 = `policies/docker-runtime.md` §4（anchor 扩展沿用 D-017 先例：**enum 数量不变**，只扩既有行的 surface anchor） |
| `ci-blocking-gate-toggle` | `.github/workflows/ci.yml` `continue-on-error` flip 或新增 blocking gate | per Stage C C-a 流程；M-FU plan 必先 register |
| `bulk-content-purge-or-migration` | ≥10 file delete/move 或 archive ceremony | 含义吸收原 "删除 / 迁移 / 归档历史内容" + "大规模目录迁移（≥10 文件）" |

补充 procedural HITL（不绑单一 surface anchor；走 PR review 流程，不入上表 canonical enum）：
- ADR `state` 变化（`draft → active` / `active → deprecated` / `supersede`）
- Phase 边界（Stage entry / closure；per Phase M2/M3 kickoff outline）

> **Post-merge tail（EVAL-backlog 自动开单）**：`runtime-skill-content-change` /
> `prompt-version-or-body-change` 触及的 PR merge 后，自动开 `[EVAL backlog]` follow-up Issue
> （A11 transitional-waiver 期兜底；无论本 PR 是否带 EVAL 引用）。规则体见
> `sdd/workflows/execution-loop.md §7.3`（HITL_Prompt §4.15 Rule 11 的 kernel home）。

> **执行机制**：AI 给具体差异，Owner 对目标/动作/关键内容/范围拍板。当前任务已明确批准的具体删除清单无需重复确认或额外理由；批准不扩展到其他目录、worktree、后来新增内容或不同动作。删除前核验绝对路径、Git 跟踪状态、未提交/未跟踪/被忽略内容、必要备份、文件占用及符号链接/重解析点；变化只暂停受影响项。核验通过后由 Codex 使用正常工具执行，不预设人工删除。项目授权与宿主审批分开，hook 不认证聊天授权；UNKNOWN/FORBIDDEN 继续阻断，守卫未命中不构成授权。实际拒绝时保留原始错误，依据证据区分 hook、exec-policy/危险命令检查、审批模式、权限/占用；通用 blocked by policy 无法归因时标未知。受阻步骤返回 BLOCKED_EXECUTION_ROUTE，不换工具、改写命令、编码、改权限或建 receipt 绕过；独立且已授权的工作可继续。

commit、普通 push、PR 创建、本地删除、远程引用删除分别核对动作与对象；一次批准可以明确列出多项，已有相同批准不重复索取。commit 绑定分支/HEAD/实际 staged 内容与文件集；push 绑定提交范围、目标 remote 和 tip；PR 绑定 repo/head/base/标题/正文。撤销或实质变化仅暂停受影响项。有限识别的 Git 命令由原生 hook 返回 `HOST_APPROVAL_REQUIRED` 上下文，继续交既有 prompt 规则及宿主正常审批；该状态不认证 Owner 授权，受保护编辑及 UNKNOWN/FORBIDDEN 仍阻断。

远程删除独立绑定仓库、remote、精确 refs/heads 引用、批准时及当前 tip、真实合并证据；保护 main/develop 和其他明确保护分支。两端按 Gitee → origin 分别核验及执行；只有成功查询证明不存在，才记录已删除或执行前已不存在。查询失败不等于不存在，本地分支已删或计划 completed 不替代远端证据。部分成功/结果未知先对账，成功项不重复；已知 prompt×never 未解除时不得换 remote 试探。仅网络/文件权限恢复或重复聊天批准不解除审批模式阻断；工程师恢复环境后先核实有效模式、规则/信任和当前对象，再处理剩余项。merge 仍由 Owner 人工执行，计划文档未提交单列交付待办，不自动提交或处置其他任务。

## §5 可修改路径白名单 / 必须 HITL 清单

本节不复制 §4 枚举。秘密、biz 旁路绝对禁止；普通未保护文件按当前任务授权修改。
`.codex/**`、原生 guard、infra 冻结及契约保留 Owner 必停；普通开发技能不再因生成物身份被 blanket 禁止。
`policies/**`、`sdd/**` 元规则、根及局部 AGENTS 的边界变化仍需 Owner 拍板。
Dockerfile 只有外部 registry 镜像引用是既定必停面，其余行保持至少两位 reviewer；不得借原生守卫路径粒度的保守阻断改写政策层级。
commit/push/PR/merge 的既有决定权保持；不以静态检查、权限模式或 hook 未触发推定批准。
技术权限、范围授权和服务凭据分别判断。个人配置与信任不由仓库工具修改。

## §6 每次任务输出要求

> **本节按现状填写（2026-08-11，issue #482）。** 原 TBD 指向的「12 字段输出模板」在仓内**没有
> 任何消费方**；而真正在用的输出要求**早已存在且有载体** —— root `.github/PULL_REQUEST_TEMPLATE.md`
> 的 §"AI Self-Check Checklist" 那 4 条，且**该模板行本身就反向引用本节**（写作
> "per `policies/ai-agent.md` §4 + §6"）。故本节按那 4 条真值化，**不另造一套无人消费的 12 字段**。

### §6.1 每次任务输出必答 4 条

| # | 条目 | 取值 | 判据出处 |
|---|---|---|---|
| 1 | **Codex 参与情况** | `NONE` 或描述其具体贡献 | §1（记录本任务已授权的实际贡献） |
| 2 | **HITL scenario hit** | `NONE` 或逐项列出 | §4 canonical 10-enum |
| 3 | **BDD/TDD impact** | `NONE` 或逐项列出 | `sdd/adapters/bdd-tdd.md` |
| 4 | **Subagent dispatched** | `NONE` 或逐项列出 | §2（A3 subagent split 准则） |

**PR 面另附 `HITL Trigger Inventory`**（canonical 10-enum 逐条勾选，与 §4 一一对应）。它与上表
第 2 条是**不同粒度**、不是重复：第 2 条是「本次是否命中」的摘要，Inventory 是**逐 enum 的可查
证据**。**不适用的行标 `— No`，不要删行**——删行会让 reviewer 无法区分「不适用」与「漏答」。

### §6.2 载体与差距

- **载体**：root `.github/PULL_REQUEST_TEMPLATE.md`（4 条正文 + `HITL Trigger Inventory` 全文）与
  `.github/PULL_REQUEST_TEMPLATE/` 下的 6 个类型模板（4 条正文 + Inventory 指针；#497 ⑥ 补入）。
- **无机器校验**：无任何 CI 执行体读取该 checklist；兜底 = merge review。
- **剩余差距（如实记录）**：6 个类型模板（bugfix / documentation / feature / hotfix / maintain /
  release）结构与根模板**完全不同**（**改前**只有「文档变更内容 / 变更原因 / 自检结果」三段），故
  4 条按 §6.1 表逐条内联、`HITL Trigger Inventory` **不复制**只留指针（同 §5.2 口径）；指针取用是
  纯人工动作，且 agent 侧的逐模板字段表尚未同步 —— **#538**。

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
  12 必停 surfaces (4 `src/mj_agent/` in-source + 8 `.agents/skills/mj-agent-infra-*`)
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

## §8 External-Info Handoff Discipline（ADR-034）

需要 AI 不能自取的秘密或外部状态时，给 Owner 精确的占位符命令、变量名、落点、失败判据和脱敏核验步骤。
不得让 Owner 把秘密粘贴到会话；不使用会回显秘密的 grep/config/log 命令。
应用设置仍经 `scripts/setup-env.ps1`；MCP 凭据维护由 Owner 在自己的终端运行 `scripts/mcp/setup-mcp-secrets.ps1`，仅原定具名变量，不写入应用环境文件。
真实解密、OS 凭据写入及平台可用性须独立留证；准备步骤不等于已经执行。

## §9 Protected-Path 拍板与执行路线

原生 config/hooks/rules、冻结技能、契约、元规则和受保护运行时代码遵循 §4/§5。
用户批准的范围在目标不变时可复用；hook 不能认证聊天批准，受保护编辑继续硬阻断。§4 所述有限 Git 命令仅交宿主正常审批，不输出自动 allow 或自建审批凭证。
遭技术拒绝即返回 BLOCKED_EXECUTION_ROUTE，不停用保护、不更改个人模式、不借另一工具或编码尝试同一动作。
项目与 hook 激活是工程师独立审阅步骤，仓库脚本不得自动信任。CI 只承担结构/行为证据，不替代 Owner 决定或宿主 canary。

---

> *`state: draft` — §1-§9 全部内容化（§5 / §6 于 #482，2026-08-11），本文件不再有待填充节。*
>
> *v0.5（2026-08-11）：#482 — 清空本文件仅剩的 2 个 TBD 块（§5 / §6），无一 decline；至此
> `M6-FU-POLICIES-TBD-SWEEP` 的 20 块全部处置完毕。**两块都不是「照 TBD 写正文」，而是先纠正原
> 占位块自身的错误前提**：*
>
> *— §5 的原 TBD 要求「与 root `CLAUDE.md` 的 §"What Claude May Edit" / §"What Claude Must Not
> Edit Without Approval" 两段同步」，**该两段在 root `CLAUDE.md` 中已不存在**（对位内容是
> §"必停 surfaces"）；且「可修改路径**白名单**」的框定与实现**相反** —— `permissions.allow`
> 含未加路径限定的裸 `Edit` / `Write` / `Read`，实际是**默认可写 + 逐档收窄**。故改写为 §5.1
> 四档路径模型（D 禁止 / A 逐写拍板 / P harness protected / F 默认可写）+ §5.2 三个「无 harness
> 载体但仍须拍板」的面 + §5.3 差距。**§5.3 刻意不判**「`Edit(...)` 是否覆盖 `Write` 工具」——
> 那是 issue #485 的 AC-1，不在本单预写。*
>
> *— §6 的原 TBD 指向一套「12 字段输出模板」，仓内**无任何消费方**；而真正在用的输出要求早已
> 存在 —— root `.github/PULL_REQUEST_TEMPLATE.md` 的 AI Self-Check 4 条，且**该模板行本身反向
> 引用本节**。故按那 4 条真值化，并记下差距：6 个类型 PR 模板结构与根模板完全不同，**均不含**
> 这 4 条与 `HITL Trigger Inventory`。*
>
> *两块的 vault 指针（`mj-agent-refactored-structure.md` / `spec-anchored-calm-lampson`）随占位
> 壳一并移除，内容改从实现本体取证 —— 沿用本单 PR #483（`data-boundary.md`）确立的先例。
> 章节编号 §1-§9 与头注行数均未变，故仓内既有的 `ai-agent.md:94` / `:98`（皆在 §4）等行号锚
> **不受影响**。`state` 不动（per #480 / `sdd/lifecycle.md` §4.1）。*
>
> *v0.6（2026-08-24）：Epic #499 PR-A0（governance anchor）— §4 A14 行 D-017 扩展邻接面按
> ADR-039（D-011/D-012/D-014 revised）扩面：新增 managed outputs（root `.agents.lock.json` /
> declared `.codex/hooks.json` / `.codex/rules/*.rules`）、`agents_sync.py` 消费的 `_common`
> loader·renderer 模块（不含其余通用 validator helper）与 PR-B/D/E sources——typed sources
> （workflow registry / translation map / enforcement 含 `receipt_policy`）+ render templates
> （preface / readme template，**非** typed source，版本由 manifest / translation map 所有），
> Notes 列声明 owned-only reconcile ownership（ADR-039 D-012 revised）；§4 Enforce 段与 §5.2
> D-017 行同步（含 V8/V9 → V8-V11 事实修正）。纯治理文本、无实现；PR-B/D/E sources 先于落地
> 纳管。`state` 不动。*
>
> *v0.7（2026-09-03）：#497 ⑥ —— `.github/PULL_REQUEST_TEMPLATE/` 下 6 个类型模板补入 §6.1 的
> 4 条 + `HITL Trigger Inventory` 指针后，§6.2 的三句活体断言（「载体……**唯一**」/「**均不含**
> 本节 4 条」/「选用类型模板的 PR **不会被提示**」）连同「修订那 6 个模板另立单」同时失真 —— 本单
> 就是那个「另立单」—— 故在同一 PR 内修正（诱发性 stale 在造成它的 PR 里修）。§6.2 **行数不变**
> （7 行进 7 行出）。行号锚不受影响的**真实理由是首个改动落在 `:198`**、其上游整段未动 —— 仓内
> 既有的 `ai-agent.md:94` / `:98` / `:112-114` **等**锚均在其之前；「行数不变」本身推不出这一点。*
>
> *同句「只有……三段」括注的成因**分两半，不可混记**：对 `documentation.md` 它在改前**逐字为真**
> （base 恰 3 个小节），是本 PR 追加的第 4 个小节使其失真 —— 这一半**属本单诱发**，故就地加
> 「**改前**」二字讨清；对另 5 个模板的过度概括则**先于本改动**存在（各自小节数不同，可复算
> `grep -c '^#' .github/PULL_REQUEST_TEMPLATE/<f>.md`），非本单诱发，与 agent 侧逐模板字段表
> 一并入 **#538**。⚠ 此处**刻意不写死小节数** —— #497 的 ①③④ 正是被写死活值打脸的三处。*
