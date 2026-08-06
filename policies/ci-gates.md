---
type: policy
artifact: ci-gates
state: draft
version: 0.5
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-06
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: CI Gates

> Phase M0 — §Review Cadence (A6) native 段 ✓.
> 其余段（§Gate 推进策略 / §例外处理 / §豁免申请流程）在 Phase M2-M3 内容填充.

## §1 Gate 推进策略

> TBD: Phase M2-M3 — 详 `sdd/gates.md` §5 启用矩阵 + 每 gate 启用前 1 周 dry-run 校验机制.

## §2 例外处理规则

> TBD: Phase M2-M3 — gate 失败但需 ship 时的 emergency override 流程（双 reviewer + 时限
> 偿还 spec debt）.

## §3 豁免申请流程

> TBD: Phase M3 — gate 长期豁免（如某 capability 在 deprecating phase）的 ADR 申请规则.

## §4 Review Cadence（A6 — Anthropic 大型代码库最佳实践；native）

`.claude/settings.json` + `.claude/hooks/` + `.github/workflows/ci.yml` + `.mcp.json` **每 3-6
月或 model release 后强制审计**.

| 触发 | 频率 | 责任人 | 检查项 |
|---|---|---|---|
| 定期 | 季度（每 3 月） | DRI | `permissions.deny` 红线列表 + `permissions.ask` 拍板门列表（per [[../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]，两者共同构成 §5 边界） / `enabledPlugins` 漂移 / hooks 健康 / ci.yml gate 状态 |
| 模型 release | model major bump 1 周内 | DRI | 新 model 是否需新 permission 边界 / hook 是否在新 model 下仍触发 |
| MCP server 季度审计 | 季度 | DRI + reviewer | `.mcp.json` 13 server trust posture + credential mode（per A14 PR gate + `capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml`） |
| Gate 启用前 | gate blocking 切换前 1 周 | DRI | dry-run violation 数量 + 影响范围 |

**审计输出**：`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（与 `policies/documentation.md`
§Review Cadence 同周期，并入同一 evidence file）.

### §4.1 「Gate 启用前」行与既有 warning 观察期的关系（2026-07-15 Owner 拍板，#341）

当某 gate 已在 CI 以 **warning 姿态**跑过一个**明文观察期**（构成要件见 §4.1.1），上表
「Gate 启用前」行的适用方式 = **吸收时序、保留产物**：

- **时序被吸收**：warning 观察期（≥14 自然日、连续、跑真实流量）是本行 1 周 dry-run 的**真超集**
  → **不再另跑**一周 dry-run，不因此推迟翻转。
- **产物保留**：`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md` 仍须产出，记 **violation 数量 +
  影响范围**。它同时充当观察期「20 次连续 CI 成功 / 零 waiver / 零未关闭 warning」的可核验计数
  工件（起点锚见 §4.1.2、度量口径见 §4.1.3）；blocking 翻转拍板以它为依据。

**既有豁免**：`.codex/config.toml` MCP 投影 gate（V11）于 2026-07-14 **day-1 blocking** 落地，
**未走**本行的 1 周 dry-run —— 属 dual-agent-compat D-016「信任面不设观察期」的**明确豁免**而非
疏漏；Owner `ci-blocking-gate-toggle` 执行记录 = issue #330 comment（2026-07-14）。无明文观察期
的 gate 不享此豁免，本行照常适用。

> **§4.1.2 / §4.1.3 的来源与提升（2026-08-04，issue #403）**：二者原为
> `plans/[PLAN]_dual-agent-compat.md` §11.2(2)/(3) 的条文，由本节 `:56` **委派**引用。该 plan 于
> 2026-08-04（`e8708a9`，PR #402）转 `state: completed` —— 规范指针遂指向**已闭合的项目记录**，
> 而 blocking flip 是**持续性**治理动作（#385 当下、G14/G15 将来均需该口径）。故将其**逐字提升**
> 为本节原生条文；对该 plan 的引用降级为**历史归属**（首次拍板 = 2026-07-15 Owner，#341），
> 不再承担规范效力。提升过程**不改变**任何阈值或判据。

#### §4.1.1 「明文观察期」的构成要件（注册制）

**明文观察期 ≠ 「gate 恰好以 warning 跑了一段时间」**。构成要件 = **事先在 `plans/` 注册**，
与 `policies/ai-agent.md` §4 对 `ci-blocking-gate-toggle` 的「**M-FU plan 必先 register**」同一要求：

| 注册项 | 说明 |
|---|---|
| gate 标识 | 与 `sdd/gates.md` §2 行名、`ci.yml` 内 step/job 名一一对应 |
| CI 首挂锚 | commit + 日期，判据见 §4.1.2 |
| 适用口径 | §4.1.3（或按 §4.1.4 声明的专属口径） |
| 阈值 + 资格公式 | 如「≥14 自然日 **AND** ≥20 连续」，两腿关系须明写 |
| 自排除规则 | 翻转 PR 自身产生的 run 是否计入（见 §4.1.3 末条） |

**未注册的后果**：不构成明文观察期 → **不享**本节吸收 → 回落 §4 表「Gate 启用前」行
（切换前 1 周 DRI dry-run + violation 数量 + 影响范围），该行**无连续次数阈值**。
两条路径都要求 Owner `ci-blocking-gate-toggle` 拍板 —— 注册与否只改变**证据标准**，
不改变**谁拍板**。

#### §4.1.2 观察期起点锚 = 该 gate 的 CI 首挂 commit

时钟属于 **gate**（钉的是「该 gate 在 warning 模式下跑了多久而无误报」），**不属于**任何
里程碑或项目轨道。

- **批量翻转受最年轻 gate 约束**：多 gate 同批翻转时，绑定时钟 = 其中**最晚首挂**者。
  （同日首挂时「最年轻」与「最早」同解，规则代价为零；仍按 gate 计，以约束将来新挂的 gate。）
- **判据以 `ci.yml` 内该 gate 的首次出现为准** —— 不是脚本文件的首次提交（脚本可先于 CI 落地），
  也不是 step/job **名**的 pickaxe（名称可能后续被改写而误指）。用 **run 命令片段**做 pickaxe：

```bash
git log --oneline --reverse -S "<该 gate 的 run 命令片段>" -- .github/workflows/ci.yml
```

#### §4.1.3 「20 次连续 CI 成功」度量口径

- **计数域**：`ci.yml` 的全部 run（任意分支），**按 head SHA 去重** —— 同一 commit 的 `push` +
  `pull_request` 一对只计一次。
- **计数条件**：该 run 中**被观察 gate 的 step 或 job 输出 clean**。**执行体输出是 SoT**，
  不是 run 级 conclusion —— `continue-on-error` 会把失败掩成绿 run（job 级同理）。
- **streak 重置**：**仅**因被观察 gate 的执行体非 clean 而重置；无关 job 失败 / flake **不重置**，
  但须在审计产物中**登记**（含成因与影响范围）。
- **自排除（防循环论证）**：翻转 PR 自身分支产生的 run **不计入**其自身的资格证据 —— 计数须锚在
  **翻转分支之前的那个 commit**。注册时须明写本规则（§4.1.1）。
- **度量命令**（其输出即翻转拍板时的证据工件）：

```bash
gh run list --workflow ci.yml --limit 100 \
  --json conclusion,createdAt,headSha,event,databaseId
# 按 headSha 去重后，自 §4.1.2 的锚点日期起，逐 SHA 核被观察 gate 执行体的输出
```

#### §4.1.4 path-triggered gate 的口径细则

> **2026-08-04 Owner 拍板生效**（issue #403）—— 本节是 §4.1 提升中**唯一新增**的规则
> （§4.1.2 / §4.1.3 为逐字提升，不含新判据），故单独走拍板。
> §4.1.3 成文时面对的 gate（V8/V9/V10）**每 run 必执行**，故未处理「gate 未被触发」的情形。
> `docker-build`（#296/#385）是首个 **path-triggered** gate：job 每 run 都起，但其构建 step 仅在
> 构建相关路径变更时执行，否则 `skipped`。（成文时该 job 居 `ci.yml`、push/PR run 皆起；
> **#438 起迁独立 workflow `.github/workflows/docker-build.yml` 仅 `pull_request` 触发**——
> push run 不再产生该 job；本节三态口径不变，该 gate 审计度量改用
> `gh run list --workflow docker-build.yml`。）

对**非每 run 必执行**的 gate，§4.1.3「计数条件」按下表细化：

| 该 run 中 gate 执行体的状态 | 对 streak 的作用 |
|---|---|
| 执行且 clean | **计 1**（按 §4.1.3 head-SHA 去重后） |
| 执行且非 clean | **重置** |
| **未触发**（`skipped`） | **中性** —— 既不计数、也不重置 |

**理由**：`skipped` 的 run 对「该 gate 会不会误报」**零信息量**；把它计入会让阈值被**空绿**充满
（vacuous streak），使「20 连续」形同虚设。故阈值只由**真实执行过**的 SHA 累积。

**注册义务**：path-triggered gate 在 §4.1.1 注册时，须**额外**载明其触发路径集，
并在审计产物中**分列**「真实执行绿」与「未触发」两个计数，不得合并为单一数字。

## §5 Settings 边界（B2 团队 vs 个人）

| 文件 | 范围 | 含义 |
|---|---|---|
| `.claude/settings.json` | 团队共享（commit） | **三档 permission 全在此**：`deny` 红线（AI 取不到的 secret 面 —— `.env` / `config/secrets*.enc` + 不可逆 `Bash` 破坏面）+ `ask` 拍板门（5 项必停面，逐写 HITL）+ `allow` 白名单（scoped 工具/命令面）；另含 `enabledPlugins` + hooks 配置 |
| `.claude/settings.local.json` | 个人（gitignore） | 个人偏好覆写（如个人 Bash 豁免）；**不是 `allow` 的归属地** —— 团队 `allow` 面在 `settings.json` |

> **`deny` vs `ask` —— 勿混（per [[../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]，2026-06-20）**：
> 5 项必停面（`tools/sql/{guardrail,precheck}.py` / `prompts/system.md` /
> `skills/**/SKILL.md` / `biz_catalog/qcm_catalog.yaml`）**曾**以 `deny` 物理硬锁承载；
> ADR-034 把 HITL 模型由「AI 出草案 → Owner 手动落盘」改为「AI 提议 → Owner 拍板 → AI 落盘」，
> 该 5 面随之 **`deny` → `ask`**（逐写拍板门，`allow` 不可抑制）。故本表「红线」= **`deny` ∪ `ask`
> 两档合起来**的边界，而 `deny` 档今日**不含**任何必停文件 —— 它只保留 AI 永不该取到的
> secret 面 + 不可逆破坏面。`ask` 仅在**交互模式**成立（`auto`/`bypass` 下放宽类改动由
> classifier 硬拦）。

### §5.1 A13 — `.claude/settings.json` PR 阻塞条件（engineering-workflow track）

> 上文 §4 Review Cadence + 本节 §5 边界表把 `permissions.deny` ∪ `permissions.ask` 边界 + 季度审计
> 框定为 **审计** cadence；本子节把 A13 升格为 **PR 阻塞 ruleset** —— 任一 PR 触动
> `.claude/settings.json` 时 reviewer 必须按下表**逐条**核对，任一不满足即阻塞合并。
> 源：Meta_Framework STANDARD §7.7 A13；决策依据
> [[../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs marketplace
> 配置分离，settings.json 属项目级 in-tree）+
> [[../decisions/ADR-032_Claude_Skill_Schema_Monitoring|ADR-032]]（engineering-workflow
> 配置漂移监控）。Phase C `[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0` 落地后本节迁为
> cross-ref。

任一 PR 变更 `.claude/settings.json` 时，下表**每一条**均为 **阻塞条件**（A13；与 §4 季度审计
边界列表同源但语义不同 —— 审计是周期性巡检，本节是逐 PR 的 hard gate）：

| # | 阻塞条件 | 判定 | 不满足后果 |
|---|---|---|---|
| (a) | `permissions.allow` **不出现裸 `Bash`**（无 sub-pattern 限定） | 必须用 scoped 形式（如 `Bash(uv run *)` / `Bash(git status:*)`）；裸 `Bash` = 无界 shell 授权 | 阻塞合并；要求改 scoped pattern |
| (b) | `permissions.deny` **必须携带 secret pattern 兜底** | 含 `.env` / `secrets.enc` / API-key glob（如 `Read(./.env)` / `Edit(./.env)` / `Write(./.env)` / `Read(**/secrets*.enc)`）；与 §5 边界表 `deny` 档定义一致 | 阻塞合并；缺失即补齐 deny 条目 |
| (c) | `enabledPlugins` **增删需 PR body 描述用途与来源** | 任何 `enabledPlugins` add/remove 必须在 PR body 给出 justification（用途 + 来源 + trust posture） | 阻塞合并；要求补 PR body 说明 |
| (d) | 5 项必停面**不得脱离 `ask` 档**（per [[../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]） | 任一必停面被移出 `permissions.ask`、或被 `allow` 条目覆盖 = 拍板门失效 | 阻塞合并；要求恢复 `ask` 条目 |

**与 §4 关系**：§4 季度 / model-release 审计是 cadence 巡检（catch 漂移）；§5.1 是 PR-time
hard gate（catch 引入）。两者共用同一 `deny` ∪ `ask` 边界定义（§5 表 + 其下注），避免双源漂移。

**Cross-ref**：`.claude/skills/` 新建目录的准入规则（A13 的姊妹门，针对 skill 目录而非
settings.json）见 `sdd/adapters/claude-code-skill.md` §Scope「`.claude/` 新目录准入规则」；
`.mcp.json` server 增删（A14）见 `policies/ai-agent.md` §4
`mcp-server-trust-posture-change` + `capabilities/infrastructure/mcp-server-governance/`（capability；former MCP STANDARD archived M6 X5）。

## §6 CI gate 命名映射

> TBD: Phase M2-M3 — `sdd/gates.md` G1-G28 与 `.github/workflows/ci.yml` step 名的双向映射.

---

> *Phase M0 — §Review Cadence native；其余 TBD Phase M2-M3.*
