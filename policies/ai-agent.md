---
type: policy
artifact: ai-agent
state: draft
version: "0.10"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
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

## §2 按需委派与 effort

协调者按可划分范围、并行收益和整体完成效率选择是否委派，不规定固定人数或文件数量触发。每次传递目标、接受基线与决定位置，输入/范围/依赖/产物，实际工作区/比较基线/版本，核验与证据要求，授权/资源/停止条件及返回点。并行写使用独立工作区或明确文件归属，共享环境写由协调者安排。

独立核验者读取真实成果，按 AC 独立建立期望和复现；另一 Agent、模型或通过总结不能单独证明质量。按风险覆盖工程、领域、Prompt、供应链等视角，不规定真人或人数。

平台支持时，协调者在当前模型实际支持档位及既定预算内自主配置 effort：明确低风险任务较低，常规实施常规，复杂跨模块/故障/审查较高，实质困难或证据矛盾可升级并记依据。所有档位采用相同 AC。effort 不自动更换模型、扩大权限或新增操作；没有真实配置能力则不声称生效。任务已定资源限制优先，无统一固定人数或数字预算。

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

## §4 实质决定与任务授权 — Canonical 10-Enum

历史 enum 保留为风险定位标签，路径命中不自动要求审批。先核实差异对接受基线、数据、安全、业务、权限与门禁的实际影响。接受基线内的普通实现、四类 runtime 面的安全行为保持、兼容契约、必要重构、局部修复及验证由 Agent 自主完成，并提供行为与负例证据。

| Enum | 需要 Owner 实质决定的变化 | 基线内执行 |
|---|---|---|
| `sql-guardrail-relax` | SQL 安全不变量、数据范围或防御失效方向变化 | 保持不变量的修复/重构，安全负例回归 |
| `runtime-skill-content-change` | 业务口径、工具数据范围、外发边界或接受标准变化 | 保持上述边界的正文改善；独立领域/Prompt 视角核验 |
| `prompt-version-or-body-change` | 行为承诺、安全/业务/外发边界或模型选择变化 | 基线内正文与版本维护，EVAL 及行为证据 |
| `biz-catalog-sync` | 指标口径、可见数据范围或上游规范选择变化 | Owner 背书快照内兼容同步，漂移与依赖核对 |
| `mcp-server-trust-posture-change` | 服务、trust、权限、凭据模式、原生守卫或冻结 infra 边界变化 | 已批准方案执行；维护冻结摘要，独立Agent审阅真实配置/守卫负例，执行Agent经正常宿主机制启用项目范围信任并验证 |
| `declared-contract-change` | breaking 承诺、跨域接受标准或权限变化 | 兼容契约补齐，行为/负例回归与引用闭合 |
| `database-migration` | 超出授权的状态影响、高风险或不可逆迁移 | 具名可逆 dev 迁移按工具链、备份和恢复条件执行 |
| `secrets-grants-or-prod-config` | 权限、生产策略、外发或供应链信任来源变化 | 已批准方案执行；既有秘密不读取，新单仓App材料只在受控后台处理 |
| `ci-blocking-gate-toggle` | 必要门禁、接受标准、执行来源或保护降低/替换 | 已批准门禁改造与负例验证，失败由 Agent 定位修复 |
| `bulk-content-purge-or-migration` | 未授权删除/移动对象、不可逆损失或范围扩大 | 独立列明具名清理、备份及损失条件后执行 |

元规则、ADR 和阶段状态的实质治理变化由 Owner 决定；普通符合已定规则的正文、计划及状态记录自主维护。阶段身份或风险等级本身不产生固定人工停点。技术拒绝无法归因时标未知，暂停受影响动作而继续独立且已授权工作。

### §4.1 接受基线与执行授权

复用 Issue、Plan、tasks、PR、evidence，分别记录接受基线与操作授权。基线说明目标/使用者、范围/延期、可观察 AC、质量与必要运行条件、风险/停止条件；授权说明允许操作、精确对象、环境、权限、副作用、资源限制、失效与撤销。工具存在、凭据、技术权限、任务关联或 CI 通过均不产生授权。

一次任务授权可具名包含 stage/commit、普通 push、PR 创建和 merge；普通授权绑定任务范围，执行时核验实际 diff、HEAD/staged、remote/tip、repo/head/base/body 和有效平台批准。目标、对象、环境、权限、风险边界未实质变化且未撤销时复用，普通内容迭代不自动要求重新批准。权限变更、删除及高风险不可逆动作须独立列明；没有该动作授权先准备具体可审阅结果，再请求 Owner 决定。

### §4.2 技术路线与删除

授权不替代宿主审批。UNKNOWN/FORBIDDEN 或实际拒绝保留原始错误，按 hook、规则、组织策略、宿主权限/占用证据定位；通用 blocked by policy 无法归因时标未知，返回 `BLOCKED_EXECUTION_ROUTE`。不得换工具、编码、改写命令、建 receipt、改权限或规则绕过。独立Agent先读取真实原生配置/守卫并复现负例，执行Agent随后仅经宿主正常机制启用本项目信任、核实际加载/canary；不改个人config、不扩大权限、不绕技术拒绝。不支持的步骤如实未验证。仅新建单仓mj-agent-delivery-executor App的私钥/短期token允许由受控后台创建、DPAPI保存、签名、注入和撤销；模型、聊天、日志不可见。现有应用/MCP/DB/个人秘密永不读取，该例外不扩大服务、权限或操作授权。

删除前核实绝对目标、Git 跟踪与未提交/未跟踪/忽略内容、必要备份、文件占用和目标/后代重解析点。复用当前任务具体清单，不重复确认；变化只暂停受影响项。远端删除另绑定 repo/remote/精确 refs、批准与当前 tip、真实合并证据，main/develop 和其他保护分支保留。双 remote 逐端对账；查询失败不证明不存在。部分成功或超时先核对副作用，成功项不重复，已知拒绝须有条件变化证据后再执行。

### §4.3 独立核验与结果接受

Owner 默认依据成品、AC、证据、限制和风险接受，保留深入技术审阅权。Owner在聊天对实际成果/SHA作批准或接受决定；Agent依该真实决定以不同于作者/最后推送者的Owner身份执行平台审核，补推须重新取得有效决定/审核，批准与业务接受分记；Agent在任务授权和平台门禁满足时merge，App执行身份无admin/checks-write/bypass。仓库批准、部署授权、实际运行验收和业务接受分别记录，候选已集成不表示交付或接受。

关键门禁应受控并实际阻止违规推进。首期候选仍可改自己的检查定义，Owner 对门禁、保护及接受基线的人工审核是已接受的过渡补偿；独立受控强制核验系统、actual 采样、部署自动化及实际恢复演练延期，不能宣称已验证。

## §5 可修改路径与永久边界

按 §4 的实际影响分类执行，普通 Plan、实现、测试、文档及局部修复不逐项交 Owner。原生资产、冻结摘要和契约直接维护，已批准成组方案由 Agent 正常工具执行；信任/权限/治理标准变化仍核对具体授权。

业务库始终只经 `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`、analyst 只读工具链，禁直接 DB 客户端、写/DDL 和旁路。现有应用/MCP/DB/个人秘密不打开/打印/记录/传输，不借用其他来源凭据。仅新建单仓mj-agent-delivery-executor App的私钥/短期token允许由受控后台创建、DPAPI保存、签名、注入和撤销；模型、聊天、日志不可见。现有应用/MCP/DB/个人秘密永不读取，该例外不扩大服务、权限或操作授权。project MCP 只含既有 GitHub、Playwright、Serena、memory×5；biz×5、ssh-manager 及个人/其他来源服务永久禁入。应用和 MCP 凭据分离、仅变量名传递。Docker 供应链及生产变化按 `policies/docker-runtime.md` §4 的实际影响核验。

## §6 每次任务输出要求

> **本节按现状填写（2026-08-11，issue #482）。** 原 TBD 指向的「12 字段输出模板」在仓内**没有
> 任何消费方**；而真正在用的输出要求**早已存在且有载体** —— root `.github/PULL_REQUEST_TEMPLATE.md`
> 的 §"AI Self-Check Checklist" 那 4 条，且**该模板行本身就反向引用本节**（写作
> "per `policies/ai-agent.md` §4 + §6"）。故本节按那 4 条真值化，**不另造一套无人消费的 12 字段**。

### §6.1 每次任务输出必答 4 条

| # | 条目 | 取值 | 判据出处 |
|---|---|---|---|
| 1 | **Codex 参与情况** | `NONE` 或描述其具体贡献 | §1（记录本任务已授权的实际贡献） |
| 2 | **Risk / decision inventory** | `NONE` 或逐项列出 | §4 canonical 10-enum |
| 3 | **BDD/TDD impact** | `NONE` 或逐项列出 | `sdd/adapters/bdd-tdd.md` |
| 4 | **Subagent dispatched** | `NONE` 或逐项列出 | §2（按需委派与实际配置） |

**PR 面另附 `Risk / Decision Inventory`**（canonical 10-enum 逐条勾选，与 §4 一一对应）。它与上表
第 2 条是**不同粒度**、不是重复：第 2 条是「本次风险与决定」的摘要，Inventory 是**逐 enum 的可查
证据**。**不适用的行标 `— No`，不要删行**——删行会让 reviewer 无法区分「不适用」与「漏答」。

### §6.2 载体与差距

- **载体**：根模板 `.github/PULL_REQUEST_TEMPLATE.md` 承载 §6.1 四项报告、完整 `Risk / Decision Inventory`
  与 `Docker Impact`；`.github/PULL_REQUEST_TEMPLATE/` 下的类型模板提供对应报告及根模板取用指针。
- **结构与同步**：模板结构以实际文件为准；原生开发技能与 PR 描述 GUIDE 的字段速查须同步维护，
  并按所选模板逐项核对标题、折叠检查块、必答报告及根模板取用项。
- **校验证据边界**：当前 CI 不核验逐模板字段语义；完整性仍由逐项核对及 merge review 确认，
  不能由静态结构检查通过推定。类型模板保留取用指针，PR 正文取用根模板完整小节并逐项作答。

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

## §8.1 单仓执行App受控后台

仅新建单仓mj-agent-delivery-executor App的私钥/短期token允许由受控后台创建、DPAPI保存、签名、注入和撤销；模型、聊天、日志不可见。现有应用/MCP/DB/个人秘密永不读取，该例外不扩大服务、权限或操作授权。后台只公开脱敏状态/非秘密标识和执行证据，不输出私钥、JWT或安装token；文档或授权不证明后台已实现。原应用/MCP秘密维护方法保留历史及其边界，不列作本次App启动前置。撤销新App token/临时Workflows write及关闭临时通道由Agent在授权内执行并逐项验证。

## §9 风险上下文与实际执行路线

原生config/hooks/rules、冻结技能、契约和元规则按§4/§5实际影响核对。有限守卫对风险路径和识别Git动作给TASK_AUTHORIZATION_CONTEXT，不认证聊天或语义；确定禁令、未知/异常输入保持block，未命中不等于授权。任务范围未实质变化复用授权；实际拒绝保留原错并返回BLOCKED_EXECUTION_ROUTE，不建凭证、换工具、编码、改写命令或放宽权限绕过。

独立Agent先读取真实原生配置/守卫并复现负例，执行Agent随后仅经宿主正常机制启用本项目信任、核实际加载/canary；不改个人config、不扩大权限、不绕技术拒绝。不支持的步骤如实未验证。CI提供结构/行为证据，有效平台审核、授权及Owner业务接受另记录。

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
>
> *v0.9（2026-10-10）：#538 —— §6.2 按实际模板修正载体与字段同步责任，补明根模板的 Docker Impact
> 取用及逐模板语义校验边界；移除「只有三段」与「字段表尚未同步」的活体断言，历史修订记录保留。
> 本次具体政策差异经 Owner 批准；`state`、Owner 决策权与审批边界不变。*

> *v1.0（2026-10-12）：ADR-042——按语义影响分类，任务授权复用、阶段检查点、独立核验与结果式接受；永久数据/秘密/技术边界不变，宿主与平台启用须真实证据。*
