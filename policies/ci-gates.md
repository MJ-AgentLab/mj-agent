---
type: policy
artifact: ci-gates
state: draft
version: 0.6
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: CI Gates

> 全 6 节均已成文（#482，2026-08-11）：§1 Gate 推进策略 / §2 例外处理规则 / §3 豁免申请流程 /
> §6 CI gate 命名映射 四节自 Phase M0 起为 TBD 占位，本轮按现状填写；§4 Review Cadence（A6）+
> §4.1 注册制观察期与 §5 Settings 边界（含 §5.1 A13）为既有 native 段。
> **运行态 SoT 始终是 `.github/workflows/ci.yml` + 三个独立 workflow**；本文件是规则 + 指针层，
> 不复制姿态真值（逐 gate 真值列在 `sdd/gates.md` §1-§3）。

## §1 Gate 推进策略

> **原 TBD 的两个指针都已失效，本节按现状重写（2026-08-11，issue #482）**：(1) 它指向
> `sdd/gates.md` §5「启用矩阵」，而该节标题现在自陈是「**历史阶段计划；现状 SoT = ci.yml**」，
> 不再描述现状；(2) 它指向「每 gate 启用前 1 周 dry-run」，而 §4.1（2026-07-15 Owner 拍板，
> #341）已把该要求限定为**注册制观察期的回落路径**。**故本节只写规则 + 指针，不复制 §5 矩阵，
> 也不复制 §4.1 的阈值。**

推进 = 把一个 gate 从「跑但不拦」变成「跑且拦」。四条规则（F1-F4；ID 为本文件局部，
与 `sdd/gates.md` 的 `G<n>`/`V<n>` 命名空间无关，见 §6）：

| # | 规则 | 执行载体 | 载体强度 |
|---|---|---|---|
| **F1** | 任何 gate 的 blocking 姿态翻转 = HITL `ci-blocking-gate-toggle`，**逐 gate 一次拍板 + 一条独立执行记录 comment** | Owner 拍板纪律 + merge review | **纪律**（无 CI gate 读取姿态变更本身） |
| **F2** | **新增** warning gate、**收窄/扩大**触发面、迁移载体（step→job、ci.yml→独立 workflow）——只要 `continue-on-error` 的**值**不变 —— **不是**翻转，不需该拍板 | 判例族 #438 / #440 / #441 / #447 / #444 / #455 | **纪律**（判例，非机器判定） |
| **F3** | 证据标准二选一：**已按 §4.1.1 注册**观察期 → 走 §4.1 的 streak 吸收；**未注册** → 回落 §4 表「Gate 启用前」行（切换前 1 周 DRI dry-run + violation 数量 + 影响范围，**无连续次数阈值**） | §4.1.1 / §4 表「Gate 启用前」行 | 文档规则 + `plans/` 注册工件 |
| **F4** | 翻转前必须先确认**该 gate 的姿态载体是哪一种**，再决定改什么；`continue-on-error` 不总是那根杠杆（见下表） | 无 | **零校验** —— 全靠落笔前核实 |

### §1.1 姿态载体有四种（`continue-on-error` 只是其一）

`sdd/gates.md` 头注把真值集合定义为「`blocking@ci` = ci.yml 有 step 且无 `continue-on-error:
true`」。**该定义只对下表前两种载体成立**；对后两种会误判。实测（`f29f501`，逐条读执行体）：

| 载体 | 判据 | 现役实例 |
|---|---|---|
| **step 级** `continue-on-error` | `jobs.<j>.steps[i].continue-on-error` | `kernel-section-refs` / `check-stale-docs` / G14/G15 / G3 / G7 / G23 / G25 / V2 / V6 |
| **job 级** `continue-on-error` | `jobs.<j>.continue-on-error` | `docker-image-build`（`docker-build.yml`）/ `check-commit-messages` |
| **退出码语义** | 执行体 `main()` 每条路径 `return 0` —— 翻 `continue-on-error` 是**空操作** | `find_old_completed_plans.py`；`find_stale_docs.py`（#440 正因此判定不追求翻转） |
| **环境变量阈值** | CI 是否设该脚本的 strict 开关 | `check_wikilinks.py`（ci.yml 设 `MJ_AGENT_A4_STRICT=1` → **blocking**）／ `check_no_cross_repo_refs.py`（`MJ_AGENT_CHECK_REFS_STRICT` **未设** → 实为 **warning**） |

另有**阈值轴**（与 blocking 轴正交，单独翻不产生 blocking）：`--fail-on error→warning`（V8/V9）
／ `--strict`（G21/G22）。V10/V11/`docker-image-build`/`check-commit-messages` **无**此轴。

> **差距陈述（不在本 PR 收紧）**：按 `sdd/gates.md` 头注的定义读，`check_no_cross_repo_refs.py`
> 与 `find_old_completed_plans.py` 都会被读成 `blocking@ci`，而两者**都不能让 CI 变红**。
> 现有 gate 行**无一被误判**（这两个执行体本就没有 gate 行，见 §6），故这是**定义的普适性不足**、
> 不是既有真值错误。改写该定义属 `sdd/gates.md` 的独立变更。

### §1.2 翻转不等于锁死合并按钮

两个 ruleset（`protect-develop` / `protect-main`）的 `required_status_checks` **各自只列
`ci` 一个 context**（实测 `gh api repos/:owner/:repo/rulesets/:id`）。故居于 `ci` job 之外的
gate（`docker-build.yml` / `check-stale-docs.yml` / `check-commit-messages.yml`）翻成 blocking
后**只是变红，不机械阻塞合并**。把它们加入 required contexts 是**可选硬化**、属仓库设置面的
独立动作，**不是**翻转的前置。`sdd/gates.md` 已逐行记这条边界注记；此处是其一般化陈述。

## §2 例外处理规则

> **本节按现状填写，而非按原 TBD 设想（2026-08-11，issue #482）**。原 TBD 描述的是一套
> 「双 reviewer + 时限偿还 spec debt」的 emergency override 流程。实测：**override 机制确实
> 存在且每天在用，但它不是那一套** —— 它无前置条件、无第二 reviewer、不留仓内工件。
> 如实记录现状，并明写差距。

| # | 规则 / 事实 | 载体 | 载体强度 |
|---|---|---|---|
| **X1** | 「gate 失败但需 ship」**只对 `ci` job 成立**。其余 gate 变红不锁合并按钮（§1.2），无需 override | ruleset `required_status_checks`（只列 `ci`） | **机器**（GitHub ruleset） |
| **X2** | 对 `ci` 的 override = **ruleset bypass**。两个 ruleset 的 `bypass_actors` 均为 `RepositoryRole` × `bypass_mode: always` —— 持有该角色者**任何时候**可越过红 `ci` 与 review 要求合并 | GitHub ruleset 配置 | **机器**（但**无条件**：无审批、无理由字段、无日志留在仓内） |
| **X3** | spec 债务偿还时限**只在 hotfix 线有规定**：`sdd/workflows/hotfix.md` 步骤 7 —— 默认 **5 工作日**、critical hotfix **3 工作日**，走 `evolve-capability.md` 补 `requirements.md` / `contracts/` + `evidence/postmortems/` | `sdd/workflows/hotfix.md` | **纪律**（无自动催办；该文件自身 `state: draft`） |

**三条差距（明写而非默默吸收）**：

1. **「双 reviewer」在 gate-失败面没有载体。** ruleset 只要求 `required_approving_review_count:
   1`。仓内仅有的 ≥2 reviewer 规则是 `sdd/workflows/hotfix.md` HITL Triggers（触及 prod compose
   → ≥2；触及 4 项专属必停 → ≥2 + 1 domain expert）与 `policies/docker-runtime.md` §4
   （Dockerfile 非镜像引用行 → ≥2）—— **三者都以「改动面」为条件，没有一条以「gate 失败」为条件**。
2. **X3 治的是 spec-first 绕过，不是 gate 失败。** `hotfix.md` 的「允许临时绕过部分 spec-first
   流程」指的是先写代码后补 spec；它**不**为「带着红 gate 合并」设定任何偿还义务。**gate 失败后
   ship，目前无偿还义务、无跟踪工件。**
3. **X2 不留证据。** bypass 合并按构造不产生仓内工件，故本仓的 evidence 账本里**不会**、也从未
   出现 emergency override 的执行记录体裁 —— 「查不到记录」在此**不等于**「没发生过」。

> **收紧属独立变更**：要把上述任一差距变成真规则，须动 ruleset（收窄 `bypass_actors`、或把更多
> context 加入 required checks）或给 `hotfix.md` 补 gate-失败分支 —— 两者都在本填充的范围外。

## §3 豁免申请流程

> **部分填充 + 部分 DECLINE（2026-08-11，issue #482）**。原 TBD 设想「某 capability 进入
> deprecating phase → 按 ADR 申请 gate 长期豁免」。实测该场景**至今零发生**，且真发生时已被现有
> 机制覆盖（见下 W3 与 DECLINE 段）。真正缺规则的是**另一类豁免** —— 它已有 **2 个先例**，
> 程序也已成形，只是从未成文。本节把那一类写成规则。

**先厘清「豁免 / waiver」在现役口径里的两个义项**（二者常在同一段里出现，混用会读错判据）：

| 义项 | 含义 | 出处 |
|---|---|---|
| **义项 A —「零 waiver」** | 观察期**资格判据**之一：窗口期内没有「gate 报了、照样 ship」的事件。度量 = 全窗口 check-run annotation 数为 0 | §4.1「产物保留」段、`plans/[PLAN]_dual-agent-compat.md` §11.1 / D-009、`plans/[PLAN]_m-fu-docker-build-gate-flip.md` |
| **义项 B —「豁免」** | 对 §4 表「Gate 启用前」行（1 周 dry-run）的**免除**，使 gate 得以 day-1 blocking | §4.1「既有豁免」段、`sdd/gates.md` V11 行「豁免注记」、`ci.yml` A6-audit step 注释 |

**本节规则治的是义项 B。**（义项 A 是被度量的属性，不是可申请的东西。）

| # | 规则 | 载体 | 载体强度 |
|---|---|---|---|
| **W1** | 义项 B 豁免 = `ci-blocking-gate-toggle` 拍板的一种，**不另设申请流程、不需 ADR**。要件三条：① Owner 拍板；② 在 issue / PR 留**独立执行记录 comment**；③ 在该 gate 的**承载物**里写明判据 —— 并写明**它不是哪一类豁免**（防后来者误援引） | Owner 拍板纪律 + merge review | **纪律** |
| **W2** | 先例即模板，**两条且互不同型**：**categorical** —— V11 MCP 投影面，事前在 `plans/[PLAN]_dual-agent-compat.md` D-016 拍板「信任面不设观察期」，记录 = #330 comment；**ad-hoc** —— A6 audit schema gate（`check_ai_context_audit.py`），Owner 2026-07-20 逐案批准，记录 = #359，判据写在 `.github/workflows/ci.yml` 该 step 注释里，且**明写「This is NOT the D-016 信任面 exemption」** | `plans/` 决策条目 ／ `ci.yml` 注释 | **纪律** |
| **W3** | **状态驱动的自动豁免不需申请**：G8 仅在 capability `lifecycle_state == "active"` 时触发、G24 仅在 `bugfix/*` 触发、`check-commit-messages` 对 release PR（`base=main` ∧ `head=develop`）在 step 层跳过 | 各 gate 执行体 / workflow 谓词 | **机器**（已实装） |

**已实装的第三类：per-target 带 justification 的豁免**（同样不走申请，写在被检对象里）——
G21「evidence `pass_rate: 1.0` **或** runbook justification fallback」、G22「未自动化的
`@risk:critical|high` scenario 必须在 `runbook.md` 给 4 字段 justification（原因 / 替代验证手段 /
升级触发条件 / 预计时间）」。**要豁免一个具体 scenario，写 justification，不发起流程。**

> **DECLINE —— 不新增「capability 长期豁免的 ADR 申请规则」。** 三条理由，均可复核：
> (1) **场景零发生**：仓内 6 个 capability 实测为 5 × `active` + 1 × `drafting`
> （`grep -rn lifecycle_state capabilities/*/*/spec.yml`），**无一** `deprecated`；
> (2) **真发生时已被覆盖**：`active → deprecated` 本身已要求 **ADR + HITL**
> （`sdd/lifecycle.md` §3 Capability 状态转移触发条件），而一旦落到 `deprecated`，W3 的 G8
> 触发条件即自动停判 —— 无需第二份「豁免 ADR」；
> (3) 为零实例的场景先造流程，只会多一条无人走、必然陈旧的规则。
> **复活条件**：出现第一个 `deprecated` capability，**且**它被某 gate 判红、**且** W3 未覆盖该
> gate —— 三条同时成立时回到本节补规则。

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

> **引用锚点注记（2026-08-11，#482）**：上表最后一行「**Gate 启用前**」在仓内被大量引作
> **`policies/ci-gates.md` §4:41**（`ci.yml` A6-audit step 注释 · `sdd/gates.md` V11 行 ·
> `decisions/ADR-038` · 多份 `plans/**` 与 `CHANGELOG.md`）。**那个 `41` 是行号，本轮
> §1-§3 填充后已失效**——该行位置随正文增长而移动。**行内容与语义未变**，仅位置变。
> **书写纪律**：引用本文件请用**章节号 + 行名**（如「§4 表「Gate 启用前」行」），**不要用行号**
> —— 行号锚会被任何上方编辑静默打断，且**没有任何 gate 能发现**（`check-stale-docs` 只匹配完整
> backtick 路径字面量，`kernel-section-refs` 只判章节号存在与否，两者都读不出 `:41`）。
> 既有的 `§4:41` 引用**有意不逐处改写**：其中多数落在 `plans/**` / `CHANGELOG.md` /
> `evidence/**` 等历史账本，改写等于篡改当时的如实记录（同 `sdd/gates.md` `check-stale-docs`
> 行 #447 的体裁判定）；活体面（`ci.yml` 注释 / `sdd/gates.md` V11 行 / `ADR-038`）的 re-point
> 列为**独立 follow-up 候选**，不在本填充内。

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

> **本节刻意不写映射表（2026-08-11，issue #482）。** 原 TBD 要的是「`sdd/gates.md` G1-G28 ↔
> `ci.yml` step 名的双向映射」。**一张手抄的双向表必然漂移** —— 两侧都在动（gate 行按 issue 逐条
> 增补、step 名随重构改写，`sdd/gates.md` 已因此明令 pickaxe 用 **run 命令片段而非 step 名**），
> 且同一事实出现两次就必有一次先陈旧。**故本节给口径 + SoT 指针 + 可复跑推导，并如实登记推导
> 推不出来的残余。** 原 TBD 的「G1-G28」措辞本身也不准确：**`G18` 不存在**（`G1-G17` 在 §1、
> `G19-G28` 在 §3），且它遗漏了 `V1-V13`（#499 PR-C2 起含 V12、PR-D1b 起含 V13）与 6 个具名 CI-infra gate。

### §6.1 映射口径（M1-M2）

| # | 规则 |
|---|---|
| **M1** | **连接键是执行体路径，不是名字。** `sdd/gates.md` 的**脚本列** ↔ workflow step 的 `run:` 命令。step 名与 gate 行名都是**可改写的装饰**，不作判据 |
| **M2** | **映射是多对多，不是双射**：一个执行体可承载多个 gate（`check_traceability.py` → G2 + G5；`check_archive_manifest.py` → G11 + G12；`agents_sync.py` → V10 + V11 + V13，按 `--surface` 分流）；一个 gate 可以**没有**执行体（`G4` / `G6` = `manual-canonical`，`G10`/`G13`/`G16` = `reserved`，`G27`/`G28` = `deferred`，`G26` = `withdrawn`）。**「gate 数」与「CI step 数」不可互推** |

**可复跑推导**（结果即映射，无需维护第二份表）：

```bash
# 左侧：gate 行 -> 执行体
grep -oE '^\| (G[0-9]+|V[0-9]+ [A-Za-z-]+|[a-z][a-z0-9-]+) \| `?[^|]*\.py' sdd/gates.md
# 右侧：CI 实际调用的执行体（三个独立 workflow 也在内）
grep -rhoE 'scripts/[A-Za-z0-9_/]+\.py' .github/workflows/
# 差集即 §6.2 的残余
```

### §6.2 残余：6 个 CI 执行体没有 gate 行（实测 `f29f501`）

推导的左右两侧并不重合。以下 6 个执行体**在 CI 里真跑**，但在 `sdd/gates.md` 的任何一行的
**脚本列**里都不存在（它们只在别的 gate 行的**叙述**里被顺带提及，那是交叉引用、不是登记）：

| ci.yml step 名 | 执行体 | 实测姿态 | 姿态载体 | 有无 ID |
|---|---|---|---|---|
| `Frontmatter schema (canonical docs)` | `scripts/check_frontmatter.py` | **blocking** | 裸 step | **A2** 的自动化（`policies/documentation.md` §5.1） |
| `Wikilinks (canonical docs)` | `scripts/check_wikilinks.py` | **blocking** | env `MJ_AGENT_A4_STRICT=1` | **A4** 的自动化（同上） |
| `A6 audit schema (evidence/ai-context-audit)` | `scripts/check_ai_context_audit.py` | **blocking** | 裸 step | 无（step 名里的「A6」见 §6.3） |
| `No cross-repo refs (forward guard)` | `scripts/check_no_cross_repo_refs.py` | warning | env `MJ_AGENT_CHECK_REFS_STRICT` **未设** | 无 |
| `Old completed plans (warning-mode GC候选)` | `scripts/find_old_completed_plans.py` | warning | `main()` 每条路径 `return 0` | 无 |
| `archive/INDEX.md idempotency` | `scripts/sdd/generate_archive_index.py` | warning | step `continue-on-error: true` | 无 |

**读法**：前两行**不是治理缺口** —— 它们有编号，只是编号在 **A 命名空间**（`policies/documentation.md`
§5.1）而 `sdd/gates.md` 未回指。**后四行没有任何编号**，其中 `check_ai_context_audit.py` 是
**blocking**。是否给这四个补 gate 行 / 补编号，是 `sdd/gates.md` 的独立变更（新增登记行不改
`continue-on-error` 值 → 按 §1 F2 **不是** `ci-blocking-gate-toggle`）。

### §6.3 三个命名空间 + 两组同形陷阱

编号不止一套。引用前先判它属哪一套：

| 命名空间 | 定义处 | 覆盖面 |
|---|---|---|
| `G<n>` / `V<n>` + 具名 CI-infra gate | `sdd/gates.md` §1 / §2 / §3 | spec gate + CI infra 守卫 |
| `A1`-`A14` | `policies/documentation.md` §5.1（A1-A6）+ §5.3（A7-A14 分派：A7-A11 → `sdd/adapters/{runtime-skill,prompt}.md`；A12 / A13 → `sdd/adapters/claude-code-skill.md` + 本文件 §5.1；A14 → `policies/ai-agent.md` §4） | 文档 / 配置 PR 门禁 |
| `OB1`-`OB5` | `policies/documentation.md` §5.2 | **非阻塞观察项，无执行体** |

**陷阱 1 —— `A6` 是重载的，两个义项都活着**：`policies/documentation.md` **§5.1 的 A6** =
「allowlist 文档变更同步检查 CLAUDE.md」（PR 门禁，自动化列写的是「Phase 0 PR review」= 人工）；
而**同一文件 §4** 与**本文件 §4** 的标题都是「Review Cadence（**A6** — Anthropic 大型代码库
最佳实践；native）」= 季度审计节奏。`ci.yml` 的 step `A6 audit schema` 校验的是**后者**的产出物
（`evidence/ai-context-audit/**` 的 frontmatter），**与 §5.1 的 A6 门禁无关**。

**陷阱 2 —— `R-G<n>` 不是 `G<n>`**：`plans/[PLAN]_spec_anchored_refactor.md` 的风险登记用
`R-G18` / `R-G19` / `R-G23` 等编号，与 gate 编号**同形不同义**（`R-G19` 出现在 `sdd/gates.md`
G26 行的理由里，指的是风险条目）。同理 `sdd/gates.md` §1 的 `G1`/`G2` 与 git worktree 规约的
**G1/G2**（新分支必走 worktree ／ PR 必带 `--base`，见 `policies/git-branching.md`）**同形不同义**。

---

> *v0.6（2026-08-11）：#482 — 清空本文件全部 4 个 TBD 块（§1 / §2 / §3 / §6），无一 decline
> 整节，§3 内含一处子项 DECLINE 并附复活条件。要点：**§1** 摘壳 —— 原指针的两端都已失效
> （`sdd/gates.md` §5 自陈为历史存档、§4「1 周 dry-run」已被 §4.1 限定为回落路径），改写为
> F1-F4 + §1.1「姿态载体有四种」（`continue-on-error` step/job 两级 + 退出码语义 + env 阈值；
> 附差距陈述：`sdd/gates.md` 头注的真值集合定义只覆盖前两种）+ §1.2「翻转 ≠ 锁死合并按钮」
> （实测两个 ruleset 的 required context 各只有 `ci`）。**§2** 按现状而非按原设想填 ——
> override 机制存在（ruleset `bypass_actors` = `RepositoryRole` × `bypass_mode: always`）但
> 无条件、无第二 reviewer、不留仓内工件；「双 reviewer」在 gate-失败面**没有载体**，
> 「时限偿还 spec debt」只在 `sdd/workflows/hotfix.md` 步骤 7 的 hotfix 线成立（5 / 3 工作日）
> 且治的是 spec-first 绕过而非 gate 失败 —— 三条差距明写。**§3** 先厘清「豁免」的两个义项
> （义项 A =「零 waiver」资格判据 ／ 义项 B = 对 §4「Gate 启用前」行 1 周 dry-run 的免除），
> 规则只治义项 B；
> W1-W3 从 **2 个既有先例**（V11 categorical / A6-audit ad-hoc #359）反推成文；DECLINE
> 「capability 长期豁免的 ADR 申请规则」——实测 6 个 capability 无一 `deprecated`，且
> `active → deprecated` 已要求 ADR + HITL、G8 落 `deprecated` 后自动停判。**§6** 刻意不写
> 映射表（两侧都在动，抄一张必漂移），改为 M1-M2 口径 + 可复跑推导 + §6.2 残余登记
> （**6 个 CI 执行体没有 gate 行，其中 3 个是 blocking**；前 2 个有 A 命名空间编号，后 4 个
> 无任何编号）+ §6.3 三命名空间与两组同形陷阱（`A6` 重载 ／ `R-G<n>` 与 `G<n>` 同形）。
> **诱发性 stale 同批修**：本轮填充令 §4 表下移，仓内 24 处 `§4:41` **行号锚**随之失效
> （行内容与语义未变，仅位置变）—— §4 已加「引用锚点注记」把该行改按**行名**可寻，并立书写
> 纪律「引本文件用章节号 + 行名、不用行号」；历史账本里的 `§4:41` 有意不改写（体裁判定同 #447），
> 活体三处 re-point 列为独立 follow-up 候选。**姿态零 delta** —— 本 PR 不改 `ci.yml`、
> 不动任何 `continue-on-error`，故**非** `ci-blocking-gate-toggle`（#438/#440/#441/#447/#455
> 判例族）。*
>
> *Phase M0 — §Review Cadence native（§4，含 §4.1 注册制观察期）。*
