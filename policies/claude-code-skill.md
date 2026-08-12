---
type: policy
artifact: claude-code-skill
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: Claude Code Skill Governance

> in-tree workflow skill（`.claude/skills/mj-agent-*`）治理政策。§1-§6 均已内容化
> （#482，2026-08-11），本文件不再有待填充节。
>
> **本文件的口径**：只写*治理规则*与*执行载体强度*。SKILL 计数 / family 分布 / gate 通过率
> 等易变事实**一律不在此硬写** —— 真值在执行体输出里，相关各节给可复跑推导命令。

## §1 3 SKILL 来源严格区分

**规则 S1（先分类，后施约束）** —— 对任何 `SKILL.md` 提出约束、写门禁或做批量改动前，**必须
先判定它属于哪一源**。三源的 schema / loader / track / 门禁**互不通用**，跨源套用是本仓反复
出现的错误类别。

**分源判据 = 路径**（唯一判据；不看文件内容、不看文件名）：

| 判据（路径前缀） | 源 | 本 policy 治理？ |
|---|---|---|
| `src/mj_agent/skills/<name>/SKILL.md` | in-source runtime（业务；进 LLM 上下文） | ❌ → `sdd/adapters/runtime-skill.md` |
| `.claude/skills/mj-agent-<group>-<verb>/SKILL.md` | in-tree workflow（工程编排） | ✅ **本 policy** |
| marketplace 仓 `plugins/<plugin>/skills/<skill>/SKILL.md` | marketplace plugin | ❌ 不在 mj-agent 治理面 |

**对照表刻意不在此复制**：三源的 schema / loader / track 字段对照表的 kernel home 是
`sdd/constitution.md` §3.3，`sdd/adapters/claude-code-skill.md` §Scope 另有 adapter 视角的
同款表。同一张表出现三次必然漂移 —— 本节只给**判据**与**治理入口**。

**规则 S2（治理入口按源分派）** —— 各源当前实际的规则 / 契约 / 执行体（2026-08-11 实测）：

| 源 | 规则 home | 契约 | CI 执行体 |
|---|---|---|---|
| in-source runtime | `sdd/adapters/runtime-skill.md` + `sdd/adapters/prompt.md` | `runtime-skill.contract.yml` | `check_runtime_skill_contracts.py`（V7）|
| in-tree workflow | **本 policy** + `sdd/adapters/claude-code-skill.md` | `claude-skill.contract.yml` | `check_claude_skill_contracts.py`（V4）|
| marketplace plugin | — | — | — |

**规则 S3（跨源改动分开提 PR）** —— 一个 PR 同时改 in-source 与 in-tree SKILL 时，两者触发的
必停面不同：in-source body 改动是 `runtime-skill-content-change` canonical 必停，且须在**同一
commit** re-freeze 对应契约的 `content_hash` + `frozen_at`（否则 V7 报 body content hash
drift）；in-tree 改动**不**触发该必停、也无 freeze 义务（`mj-agent-infra-*` 八件的 content-hash
freeze 是另一套，见 `policies/ai-agent.md` §7）。两者混在一个 PR 会让 reviewer 无法按面核对
⇒ 拆分。

> ⚠ **指针新鲜度注记**：`sdd/constitution.md` §3.3 的 "Governance" 一列仍写作
> "Track B（Agent_Side v1.x…）" / "Track C（Meta v2.x §3.10；**Phase M5 后并入**
> `sdd/adapters/claude-code-skill.md`）"。该 "并入" 已于 M6 PR4 完成（ADR-031），tri-track
> 三件已停用，故那两处未来时表述应读作**已生效**。该表的路径 / schema / loader 三列**仍准确**，
> 只有 Governance 列的时态过期。修订另立单，不在 #482 面内。

## §2 ADR-013 Native Schema（2 字段）

**规则 N1（字段集封闭）** —— `.claude/skills/*/SKILL.md` 的 frontmatter **只含 `name` +
`description` 两个键**，多一个键即 deviation。这与 in-source runtime SKILL 的 13 字段
Agent_Side schema **无交集**，两者不得互相套用（per §1 S1）。

**规则 N2（description 是唯一触发机制）** —— Claude Code 主 process 靠 `description` 做 skill
触发匹配，`name` 只作标识。故 description 同时承担正向触发与反向剪枝两个负载，质量门为三条：

1. `len(description) >= 200`
2. 含反向触发块，字面量 `Do not use for:`
3. `name` 等于其目录名，且匹配 §3 的 namespace 模式

**ADR 归属须精确** —— ADR-013 的五个决策点治的是 **marketplace plugin**（决策点 1 / 2 / 4 / 5）
与 **in-source 不变**（决策点 3）；**没有任何一个决策点提到 `.claude/skills/`**（ADR-013 早于
in-tree 生态的 ADR-016）。in-tree 沿用这套 2 字段 schema，是由 **ADR-016 决策点 1 的表格** +
**`sdd/adapters/claude-code-skill.md`** + **`policies/documentation.md` §5.1
engineering-workflow 补丁**三处共同确立的**扩展适用**；"ADR-013 native" 是沿用其 schema 名，
不是援引其决策范围。写新规则时勿把 in-tree 条款回填进 ADR-013。

**当前实装状态（可复跑，勿照抄数字）**：

```bash
uv run python scripts/sdd/check_claude_skill_contracts.py --all | tail -3
```

2026-08-11 实测：全部 on-disk SKILL **PASS**，`WARN 0 / FAIL 0`，且**每一个**都带 2 字段
frontmatter —— 早期那个 "markdown-body-only"（`name` 由目录名推断、`description` 由正文首段
推断）的全局 deviation **已消解**。

> ⚠ `sdd/adapters/claude-code-skill.md` 的 §Current mj-agent Implementation Status 与 §CI Gate
> 两节仍在描述那个已消解的 deviation（"34/34 全员 markdown-body-only"、"预期 ~34 WARN"、
> "M2 warning / M3 blocking"，以及待决的 Option A / Option B），与上面的实测**相反**。
> **以实测为准**；修订该 adapter 另立单。

## §3 Namespace Convention（ADR-016）

**规则 P1（三段式命名）** —— `mj-agent-<group>-<verb>`，目录名即 skill 名：
`.claude/skills/mj-agent-<group>-<verb>/SKILL.md`；slash command 自然成形
`/mj-agent-<group>-<verb>`。`<verb>` 是 kebab-case 动作短词，可多段（如 `studio-probe` /
`skill-doc-improve`）。

**规则 P2（group 是封闭枚举）** —— `<group> ∈ {flow, git, doc, runtime, infra}`，5 个固定
family，**扩展需另开 ADR**（ADR-016 决策点 1 原文）。该枚举在实现里是硬编码的：
`check_claude_skill_contracts.py` 的 namespace 校验只认这 5 个 group，第 6 个 family 必产
finding。

**各 family 语义**：`flow` = 编排器（跨 stage 调度）· `git` = git 域工具 · `doc` = 文档域工具 ·
`runtime` = in-source canonical 的 propose→拍板→apply（见 §4）· `infra` = 项目基础设施。

**计数刻意不在此硬写** —— 总数与 family 分布都是易变量，SoT = 执行体输出：

```bash
uv run python scripts/sdd/check_claude_skill_contracts.py --all | tail -1
ls -d .claude/skills/*/ | sed -E 's#.*/mj-agent-([a-z]+)-.*#\1#' | sort | uniq -c
```

> ⚠ **已知过期计数（勿照抄）**：ADR-016 决策点 1 的 family "数量" 列是**决策当时的目标态
> 快照**。其自身 2026-06-22 补记已声明 SoT = 上述执行体，并把 `flow` 由 9 更正为 10；但同表
> `infra` 一列至今未随实装更新。
>
> ⚠ **一处规则冲突（如实记录，本单不裁决）**：`sdd/adapters/claude-code-skill.md` §Scope 的
> 「`.claude/` 新目录准入规则」表写「新 skill family 目录 = **普通 PR 直接新增**，无需 kernel
> 修订……新增第 6 family 走此路径」，与 ADR-016 决策点 1 的「**不允许扩展（除非另开 ADR）**」
> 直接相反。**实现站在 ADR-016 一侧**（正则枚举硬编码）。裁决另立单。

## §4 Runtime Family Propose→拍板→Apply（ADR-034）

`.claude/skills/mj-agent-runtime-*` 4 个 skill 遵循 **propose→拍板→apply**：先提议 diff +
impact，停在工具中立 `OWNER_APPROVAL_REQUIRED` 停点；Owner 拍板后由 skill 直接落盘（Claude Code
载体 = AskUserQuestion + settings `ask` 权限门；Codex 载体 = AGENTS.md 自守 prose）。未经拍板
不写 `src/mj_agent/skills/`、`prompts/`、`agent.py`、`tools/`、`biz_catalog/`.

执行机制：A12 description quality gate + SKILL.md ## Anti-patterns 段 + `.claude/settings.json`
`ask` 逐写拍板门三重保险（ADR-034 deny→ask；详 `policies/data-boundary.md` §3）.

## §5 A12-A14 PR Gate Self-Check Checklist

> A12-A14 是 **engineering-workflow track 专属**的三道 PR 门禁，仅在 PR 触及 `.claude/**` /
> `.mcp.json` 时生效。编号的**分派** home 是 `policies/documentation.md` §5.3；本节是**执行
> 面** —— 逐条自检项 + 各自的实际载体与强度。根 `.github/PULL_REQUEST_TEMPLATE.md` 顶注所称
> 「旧 tri-track A1-A14 self-check 迁入 `policies/documentation.md` + `policies/claude-code-skill.md`
> 段」，A12-A14 那一半由本节承接。

### §5.1 逐条自检项

六个类型 PR 模板（`.github/PULL_REQUEST_TEMPLATE/*.md`）均内置同名
`Engineering-Workflow checklist (A12-A14)` 折叠块，勾选即留痕：

| # | 触发路径 | 自检项 |
|---|---|---|
| **A12** | `.claude/skills/**/SKILL.md` | frontmatter 只有 `name` + `description`（§2 N1）；`description` ≥ 200 chars、含正向触发短语、含 `Do not use for:` 反向块（§2 N2）；`name` 等于目录名且匹配 `mj-agent-<group>-<verb>`、group 在 5 枚举内（§3 P1 / P2） |
| **A13** | `.claude/settings.json` | (a) `permissions.allow` 无裸 `Bash`（必须 scoped）；(b) `permissions.deny` 携带 secret pattern 兜底；(c) `enabledPlugins` 增删在 PR body 给出用途 + 来源 + trust posture；(d) 必停面不得脱离 `ask` 档 |
| **A14** | `.mcp.json` 及其 D-017 派生面 | server 增删声明 trust posture（first-party / third-party / first-party-wrapper / community）+ credential mode（none / OAuth / api_key_via_env / wrapped_script_url_override / template_var）+ rationale；trust posture 降级须附 issue 或 mitigation |

**规则体刻意不在此复制**：A13 四条的判定与「不满足后果」列在 `policies/ci-gates.md` §5.1；
A14 的 PR body 模板全文 + trust-posture 降级触发条件在
`capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml` 的
`a14_pr_gate` / `trust_posture_downgrade` 两段，其必停 enum 锚点是 `policies/ai-agent.md` §4
的 `mcp-server-trust-posture-change`。

### §5.2 载体强度 —— 三条**互不相等**

> 与 `policies/docker-runtime.md` §1 同款纪律：把「有规则」与「有机器校验」分开记，别让读者
> 默认「CI 会拦」。

| # | 机器载体 | 实际强度 | 依据（2026-08-11 实测） |
|---|---|---|---|
| **A12** | 有 —— `scripts/sdd/check_claude_skill_contracts.py`，CI 步骤 V4，步骤级无 `continue-on-error` | ⚠ **行为上是 warning** | 该执行体的**全部** finding 均为 `Severity.WARN`，无任何 FAIL 路径；而 CI 调用**不带** `--strict`，`Summary.exit_code(strict=False)` 仅在 FAIL 时返回 1 ⇒ **恒返回 0**。负向控制：一个五项全违规的 SKILL 产出 `WARN 5 / FAIL 0 / exit 0`；同一输入加 `--strict` 则 `exit 1`。 |
| **A13** | **无** | 纯人工 | 全仓无校验 `.claude/settings.json` 内容的执行体；`.github/workflows/**` 无任何步骤读取它（`check-stale-docs.yml` 里的 `.claude/**` 只是**触发路径过滤器**，不校验 settings 语义）。载体 = PR 模板勾选 + reviewer。 |
| **A14** | **无** | 纯人工 | `governance.contract.yml` 的 `a14_pr_gate.automation` 声明 M2 warning / M3 blocking 由 `scripts/sdd/check_a14_gate.py` 承担，但**该脚本在仓内不存在**，亦无任何 workflow 引用它。载体 = PR 模板勾选 + 根模板必停清单行 + reviewer。 |

**A12 的姿态登记与行为不一致（如实记录）** —— `sdd/gates.md` 的 V4 行登记为 `blocking@ci`，
`ci.yml` 的 V4 步骤名亦写 "BLOCKING"；但同一 workflow 在 V1-V6 上方的注释块写的是
"V2 / V4 / V6 kept warning"。三处口径两两不同，**行为真值以上表实测为准**（恒 exit 0）。
成因是 `policies/ci-gates.md` §1.1 已登记的**姿态载体 ③（退出码语义）**：步骤级
`continue-on-error` 被摘掉了，但正交的**阈值轴** `--strict` 从未加上，故那次翻转是空操作。
把 A12 变成真 blocking = 给 V4 加 `--strict`，属 `ci-blocking-gate-toggle` 必停（一 gate 一
拍板 + 独立执行记录），**不在 #482 面内**，另立单。

## §6 MCP Server Governance

**治理 home** = `capabilities/infrastructure/mcp-server-governance/`（capability）。原
`[STANDARD]_MJ_Agent_MCP_Server_Governance` 已于 M6 X5 停用并归档，其条款**已折入该
capability**：`contracts/governance.contract.yml` 承接 `a14_pr_gate`（PR body 模板全文）/
`trust_posture_downgrade`（降级触发条件）/ `quarterly_audit`（季度审计 cadence），`design.md`
承接叙述面。决策依据 ADR-028。**引用时指向该 capability，不要再指向已停用的 STANDARD。**

**互引边界（per ADR-028）** —— 三处各管一段，互不复制：

| 面 | home |
|---|---|
| 必停 enum 锚点 + D-017 派生邻接面（`.codex/**` / `.agents/**` / `agents_sync.py` / manifest 的 `mcp` 与 `codex.posture` 段） | `policies/ai-agent.md` §4 `mcp-server-trust-posture-change` |
| A14 PR body 模板 / trust posture 分级 / credential mode 枚举 / 季度审计 cadence | 上述 capability 的 `governance.contract.yml` |
| A14 在 in-tree skill 治理面的自检位置与载体强度 | **本 policy** §5 |

**server inventory 刻意不在此硬写** —— `.mcp.json` 自身即 SoT：

```bash
uv run python -c "import json; print(len(json.load(open('.mcp.json', encoding='utf-8'))['mcpServers']))"
```

**两条永久约束（不随 inventory 变动）**：

- `pg-mj-system-biz-*` 全部 + `ssh-manager` 在 `.agents` / `.codex` 投影中钉死 `never`，按
  ADR-006 / ADR-009 数据边界**永久排除**（per `AGENTS.md`「Generated projections」）。
- biz 数据访问只走 agent 工具链；任何 MCP server 都不得成为绕过 L1 / L1b 的旁路。

**已知差距（如实记录）**：

- A14 **无机器载体**（§5.2）：`governance.contract.yml` 声明的 `check_a14_gate.py` 不存在。
- 该 capability 的 `spec.yml` `lifecycle_state` 仍为 `drafting`。
- `policies/ci-gates.md` §4 Review Cadence 表把 `.mcp.json` 写作「13 server」，与上述推导命令
  的实测值**不符** —— 以推导命令为准；修订那一行另立单。

---

> *`state: draft` — §1-§6 均已内容化（#482，2026-08-11），本文件不再有待填充节。*
>
> *v0.2（2026-08-11）：#482 — 清空本文件全部 5 个 TBD 块（§1 / §2 / §3 / §5 / §6），无一
> decline。共同取证结论与前几份 policy 一致：**规则实体大多早已在仓内，只是从未成文**。
> §1 立 S1-S3（先分类后施约束 / 治理入口分派 / 跨源改动拆 PR），**刻意不复制** 三源对照表
> （kernel home 在 `sdd/constitution.md` §3.3），并记其 Governance 列的时态已过期。
> §2 立 N1-N2 并**精确化 ADR 归属**：ADR-013 五个决策点无一覆盖 `.claude/skills/`，in-tree
> 沿用 2 字段 schema 是 ADR-016 + adapter + `documentation.md` §5.1 三处确立的扩展适用。
> §3 立 P1-P2，计数改为可复跑推导；如实记下 ADR-016 family 数量列已过期，以及 adapter
> 「第 6 family 走普通 PR」与 ADR-016「须另开 ADR」的**规则冲突**（实现站 ADR-016 一侧）。
> §5 是本轮主体：逐条自检项 + **§5.2 载体强度三条互不相等** —— A12 有执行体但
> **行为上是 warning**（全部 finding 为 WARN、CI 不带 `--strict` ⇒ 恒 exit 0；负向控制
> 五项全违规仍 `exit 0`，加 `--strict` 才 `exit 1`），A13 / A14 **无机器载体**（A14 声明的
> `check_a14_gate.py` 在仓内不存在）。并记 V4 姿态在 `sdd/gates.md` / `ci.yml` 步骤名 /
> `ci.yml` 注释块三处口径两两不同。§6 定 home 与三处互引边界，inventory 改推导命令。
> **刻意不做**：不给 V4 加 `--strict`（属 `ci-blocking-gate-toggle` 必停，另立单）；不修
> adapter / ADR-016 / `ci-gates.md` 的过期陈述（均为既存独立缺陷，另立单）。
> `state` 不动：内容填充不构成 live-kernel-home 意义上的操作必要性（per #480 /
> `sdd/lifecycle.md` §4.1）。*
