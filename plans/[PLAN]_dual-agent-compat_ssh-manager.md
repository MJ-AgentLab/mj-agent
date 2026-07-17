---
type: plan
summary: dual-agent-compat v5 ssh-manager settings allow 收窄执行计划（#312 独立拍板议题 2）——收窄 .claude/settings.json 单条 mcp__ssh-manager__* allow 通配（覆盖 37 工具，含 ssh_execute_sudo/ssh_deploy/ssh_db_import 等 24 写面，deny 无兜底）；含全工具面分类（13 read / 24 write）+ 零自动调用证据 + 三收窄口径分析（A 全删→prompt / B 子集白名单 / C 全删+destructive deny-floor）+ 推荐；Gate 5 拍板 = A 全删（allow 24→23）；1 PR（#356 maintain/356-ssh-manager-allow-narrow，PR #357 merged `c446a93`）；不改 ci.yml、不翻 gate 姿态、不动 .mcp.json/manifest/4 必停面；总锚 #312
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-17
completed: 2026-07-17
state: completed
track: shared
---

# [PLAN] 双工具兼容 v5 — ssh-manager settings allow 收窄切片（issue #356）

## 1 Linked Artifacts

- Issue：#356（本切片）；总锚 **#312**（v5 实施总锚，「独立拍板议题」第 2 项 = 本切片）
- Intake：[[[INTAKE]_dual-agent-compat_ssh-manager|本切片 Intake]]（scope-interpretation 拍板 §2/§7 + 零自动依赖 §3）
- 程序计划：[[[PLAN]_dual-agent-compat|v5 计划]]（§17 独立拍板议题 · D-013 MCP 三档 · §5.1 数据边界）
- 前序切片：[[[INTAKE]_dual-agent-compat_settings-narrow|#344 settings-narrow]]（§7 拍板项 3 = ssh 面递延本 issue 的权威锚）·
  [[[INTAKE]_dual-agent-compat_p4-gate-definition|#341 INTAKE]] §7 拍板项 6
- Vault 依据（不入仓）：`claude-codex-agent-kernel/mj-agent/[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md` §四（ssh 最终形态框定）
- 治理：[[../policies/ai-agent|ai-agent]] §4（HITL 10-enum）· [[../policies/ci-gates|ci-gates]] §5.1（A13）·
  [[../decisions/ADR-006_Fail_Safe_Reads|ADR-006]]（数据边界四层）· [[../decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]]（MCP 清单/治理）

## 2 Context

`.claude/settings.json` `permissions.allow` 现 **24 条**（`:5-28`，#344 后），其中 `:25`
`"mcp__ssh-manager__*"` 为**工具级通配**——会话内对 ssh-manager 的任意 MCP 调用**免 prompt 自动放行**，
且 `deny`/`ask` 无 ssh-manager 兜底。

**纪律张力（vault 评估 §二.1 + 本切片深化）**：#344 已把 biz-prod 由通配收为 prompt，其**可接受性建立在
ADR-006 L3/L4 兜底之上**——biz SELECT 即便绕开 L1/L1b，`default_transaction_read_only`（L3）+ analyst
GRANT + `statement_timeout`（L4）仍**在 DB 侧挡住写**。**ssh-manager 无任何等价 floor**：`ssh_execute_sudo`
以 root 在远端执行任意命令，无 DB 角色、无 timeout、无只读事务兜底。故 ssh-manager 的免 prompt 通配是
比 biz-prod **更宽**的面（无下游 floor），是 §17 独立拍板议题 2 要处置的残留面。

**scope = settings allow-list 收窄**（Owner 2026-07-17 拍板，Intake §2/§7）：非自建 proxy——ssh-manager
是直接 npx stdio server（`.mcp.json:112-115`），仓内无 proxy 机制先例。收窄口径（A/B/C）本 §5 呈方案，Gate 5 拍板。

## 3 ssh-manager 工具面分类（37 工具；证据 = MCP schema description）

> 计数随 MCP server 版本浮动（vault 2026-07-14 记 38，本会话 harness 枚举 37）——**非决策载体**。
> 决策载体 = ①零自动调用（§4）②写面广度与无下游 floor（下表）。read/diagnostic 13 项中已加载
> 的 13 个 description 逐字核验；write/state 24 项按工具名语义归类（destructive 者名即定性，
> 如 `ssh_execute_sudo`/`ssh_deploy`/`ssh_db_import`，无需再验）。

**A. read-only / diagnostic（13；description 已核验）**

| 工具 | description | 备注 |
|---|---|---|
| `ssh_list_servers` | List all configured SSH servers | 纯读 |
| `ssh_health_check` | Perform comprehensive health check | 纯读 |
| `ssh_connection_status` | Check status + manage connection pool | 含 reconnect/disconnect/cleanup = **本地连接池状态**（非远端写） |
| `ssh_db_list` | List databases or tables | ⚠ 取 `dbPassword`，**直连 DB**（绕 L1/L1b） |
| `ssh_history` | View SSH command history | 纯读 |
| `ssh_tail` | Tail remote log files | 纯读 |
| `ssh_tunnel_list` | List active SSH tunnels | 纯读 |
| `ssh_session_list` | List all active SSH sessions | 纯读 |
| `ssh_backup_list` | List available backups | 纯读 |
| `ssh_monitor` | Monitor system resources (CPU/RAM/disk) | 纯读 |
| `ssh_profile` | Manage profiles (list/switch/current) | switch = **本地 profile 状态** |
| `ssh_service_status` | Check status of services | 纯读（无 restart 参数） |
| `ssh_db_query` | Execute **SELECT-only** query | ⚠ 取 `dbPassword`，**直连 DB SELECT**（绕 L1/L1b；tool 自限只读但仍是数据边界外读路径） |

**B. write / state-change / destructive（24；名即定性）**

| 子类 | 工具 | 危害 |
|---|---|---|
| **远端执行/部署/数据（最高危）** | `ssh_execute` · `ssh_execute_sudo` · `ssh_execute_group` · `ssh_deploy` · `ssh_db_import` · `ssh_db_dump` · `ssh_upload` · `ssh_sync` · `ssh_backup_create` · `ssh_backup_restore` · `ssh_process_manager` · `ssh_session_send` · `ssh_download` | 任意命令/root/多机/部署/DB 写入/覆盖恢复/文件上传同步/进程增杀/数据外泄——**均无下游 floor** |
| **配置/管理状态** | `ssh_key_manage` · `ssh_group_manage` · `ssh_alias` · `ssh_command_alias` · `ssh_hooks` · `ssh_alert_setup` · `ssh_backup_schedule` | 改 SSH 密钥/主机组/别名/钩子/告警/计划——持久配置写 |
| **会话/隧道状态** | `ssh_session_start` · `ssh_session_close` · `ssh_tunnel_create` · `ssh_tunnel_close` | 起/关会话与隧道——网络/会话状态 |

**要点**：37 工具中 **24（65%）** 改变远端/配置/会话状态，其中 **13 个可修改或破坏远端主机/数据/配置**，
且 ssh-manager 覆盖 9 台主机（含 prod cloud `8.135.38.175`、runner、test、DGX `192.168.0.189`）。
即便「read」子集也含 `ssh_db_query`/`ssh_db_list` 两个**直连 DB、取明文 `dbPassword`、绕 L1/L1b** 的数据边界外读路径。

## 4 零自动依赖（决定性负向事实）

- 全仓无任何 skill/script/src **调用** ssh-manager 工具：
  ```bash
  grep -rn "mcp__ssh-manager__ssh_\|ssh_execute_sudo(\|ssh_deploy(\|ssh_db_import(" .claude/skills/ .claude/scripts/ scripts/ src/
  ```
  → **0 命中**（2026-07-17 实测；AC-5 在 PR 内重跑）。
- 唯一功能引用 = `.claude/skills/mj-agent-infra-app-start/SKILL.md:110,315` 的**否定**引用：agent **不**驱动 SSH，
  owner 自己终端起隧道，且「ssh-manager tunnel 有 bug——转发即 reset」。
- **推论**：收窄 ssh-manager allow **不破坏任何自动化流程**——无 skill/workflow 依赖它免 prompt。收窄的
  唯一可观察影响 = 将来若有人在会话内**手动**发 ssh 调用，由「免 prompt 自动放行」→「弹 prompt」（A/B）或
  「destructive 子集 hard-deny」（C）。

## 5 收窄口径三选项（Gate 5 拍板）

> **共同前提**：三选项都**收紧**（无 widening）→ agent 可编辑+commit；均不断连（`.mcp.json` server def +
> `settings.local.json` `enabledMcpjsonServers` 不动，ssh-manager 仍可被**显式批准后**调用）；均**仅交互模式
> 完全成立**（`bypass` 下 allow 无关、只有 `deny` 仍拦 → 见各选项 auto/bypass 行为）。

| 选项 | 动作 | 交互模式效果 | auto/bypass 模式 | 代价 |
|---|---|---|---|---|
| **A 全删** | 删 `:25` 一行 | 全部 37 工具 → 弹 prompt（= 拍板） | bypass 下**全部放行**（无 deny 兜底）；auto 由 classifier 定 | 最简、可逆、与 #344 biz-prod 同构；但 destructive 子集无 hard floor |
| **B 子集白名单** | 删通配 + 加 read 子集 per-tool allow | read 子集免 prompt、write 24 弹 prompt | bypass 全放行；auto classifier | **保留价值≈0**（零自动调用）；且「read」含 `ssh_db_query`/`ssh_db_list` 直连-DB 边界外读路径不宜免 prompt；+多行维护面 |
| **C 全删 + destructive deny-floor** | 删 `:25` + 加 destructive 子集 `deny` | destructive 子集 **hard-deny**（改 settings 方可解）、其余弹 prompt | **deny 子集在 bypass/auto 下仍拦**（唯一在非交互模式仍成立的选项） | 与 biz-prod 的 L3/L4 floor 对称（给 ssh 一个 hard floor）；但 +维护 deny-list、posture 升级（deny 现仅保留给 secrets/rm）、owner 手动 ssh 需先改 settings |

### 5.1 分析

- **B 被支配**：零自动调用 → 白名单不保留任何免 prompt 价值；且唯一「像样」的 read 子集（`ssh_db_query`/
  `ssh_db_list`）恰是数据边界外的直连-DB 读路径，**更不该**免 prompt。B 徒增维护面、换负收益 → **不推荐**。
- **A vs C = 真实权衡**：
  - **A** 关闭「免 prompt 自动放行」这个**本切片的名义缺口**——任何 ssh 调用此后都需显式批准。与 #344
    对 biz-prod 的处置**逐字同构**（删 allow → prompt，不加 deny），与仓「必停=ask/prompt、deny 仅留给
    `.env`/secrets/`rm`」的既有 posture 一致。可逆、单行、零维护。
  - **C** 额外给 destructive 子集一个 **hard floor**。理据（vault §二.1 深化）：#344 对 biz-prod 只用 prompt
    是**因为** L3/L4 在 DB 侧兜底了最坏情况；ssh destructive **无此兜底**，故「prompt-only」对 ssh 的**有效
    保护弱于** #344 对 biz-prod 的保护。C 补上这个 floor，且在 bypass/auto 下仍拦（A 在 bypass 下全放行）。
    代价：deny-list 需维护 + 选「哪些算 destructive」是判断 + owner 若将来要手动 ssh-deploy 须先改 settings +
    把 deny 从「secrets/rm 专属」扩到 ssh（posture 升级）。
- **零自动调用对两者都成立**：owner 不经 Claude 用 ssh → A 的 prompt「从不触发」、C 的 deny「从不挡真实操作」。
  差异只在**将来一次手动 ssh 尝试**时显现：A = 一键批准；C = destructive 需先改 settings。

### 5.2 推荐（非拍板；Gate 5 由 Owner 定）

**倾向 A**，因：(1) 与 #344 biz-prod 处置逐字同构、与仓 deny-reserved-for-secrets/rm posture 一致；
(2) 单行、可逆、零维护；(3) 关闭「免 prompt 自动放行」这一名义缺口已达议题目的；(4) 交互模式下 prompt 即
per-call 拍板 backstop，nothing 静默执行。

**但 C 有本切片新发现的强理据**（务必呈 Owner，不隐去）：ssh destructive **无 biz 的 L3/L4 floor**，
prompt-only 对 ssh 的有效保护严格弱于 #344 对 biz-prod 的保护；C 补 hard floor 且在 bypass/auto 下仍成立。
若 Owner 更重「非交互模式也守 + 与危害等级匹配的 hard floor」，**C 是更有原则的选择**。

> **拍板须知（承 [[[INTAKE]_dual-agent-compat_p4-gate-definition|#341]] §7.1 + 错误前提作废纪律）**：
> 上表每格效果均 file:line / 语义可核验；若拍板中发现任一前提为假（如「某工具其实是 read」），
> 原拍板作废，带更正回 Owner 重确认，不单方改写。

**若 Gate 5 选 C**：拟定 destructive deny 子集 = §3.B「最高危」13 项（`ssh_execute` · `ssh_execute_sudo` ·
`ssh_execute_group` · `ssh_deploy` · `ssh_db_import` · `ssh_db_dump` · `ssh_upload` · `ssh_sync` ·
`ssh_backup_create` · `ssh_backup_restore` · `ssh_process_manager` · `ssh_session_send` · `ssh_download`）
+ `ssh_key_manage`（密钥管理，敏感）= **14 条 deny**；配置/会话/隧道类留 prompt。最终子集拍板时定。

### 5.3 Gate 5 拍板 = A（2026-07-17）

Owner AskUserQuestion 拍板 **A 全删**：删 `.claude/settings.json:25` `"mcp__ssh-manager__*"` 一行 →
allow 24→23、deny 不变；ssh-manager 全部工具由免 prompt 自动放行 → 弹 prompt。C 的「无-L3/L4-floor →
prompt-only 弱于 #344」理据（§5.2）已如实呈 Owner，Owner 权衡后择 A（简洁 / 可逆 / 与 #344+仓 posture 一致
优先于 bypass-mode hard floor）。§7 WBS + §8 AC 按 A 口径执行；§8.1 B/C delta 作废。

## 6 Scope

**In-scope**

1. **收窄 `.claude/settings.json`** 按 Gate 5 拍板口径（A/B/C 之一）
2. **CHANGELOG `[Unreleased]` 条目**（依家族先例——历次 settings.json 改动均留条目）
3. **本 [INTAKE]+[PLAN] 落盘**（state: active；merge 后独立小 flip PR 翻 completed）

**Out-of-scope（防 scope drift；逐项有据）**

| 项 | 不做的理由 |
|---|---|
| `.mcp.json` ssh-manager server def（`:112-171`） | A14 硬停面；本切片只动 harness 权限面，不动 server 定义/凭据布线 |
| Codex 投影 / `.agents` / `.codex` | ssh-manager 已 `never`-tier（D-013）；Codex 侧已封，本切片仅 Claude 侧 |
| 自建 ssh proxy-wrapper | Intake §9-1：过滤工具/主机面的 MCP proxy = 更大工程，另立切片 |
| user-level Codex config 镜像收窄 | owner 个人 harness 决定，仅登记（vault §四 / Intake §9-2） |
| `settings.local.json` `enabledMcpjsonServers` | 不动——ssh-manager 仍**已启用**、可显式批准后调用；本切片只改 auto-approve 面 |
| memory×5 / biz allow / 4 必停面 / gate 姿态 | 与本切片正交；biz allow 已 #344 处置 |

## 7 Work Breakdown（1 PR，`maintain/356-ssh-manager-allow-narrow`）

> W1 的具体 diff 由 Gate 5 口径定。下表按**推荐 A** 写；若选 C，W1 追加 deny 子集（见 §5.2 末），AC-3 相应改（§8.1）。

| # | 动作 | 文件 | 备注 |
|---|---|---|---|
| W1 | 按拍板口径收窄 | `.claude/settings.json` | **A**：删 `:25` 一行 → allow 24→23。**C**：删 `:25` + `deny` 加 14 条 → allow 23、deny 9→23。protected path → 写入弹 prompt（= 拍板）；**收窄**方向 classifier 不硬拦 |
| W2 | `[Unreleased]` 条目 | `CHANGELOG.md` | 记「narrow ssh-manager allow（#356）」，注明口径 |
| W3 | 落盘 Intake + Plan | 本 2 文件 | `state: active`；merge 后独立小 flip PR 翻 `completed` + 加 `completed:` 字段（家族惯例） |

## 8 验收标准（全部可执行自证；承 #341「AC 逮住作者本人」教训——精确 pattern，PR 前实跑一遍）

> 下列按**推荐 A**（allow 24→23、ssh-manager 条目移除、deny 不变）。Gate 5 若选 B/C 见 §8.1 delta。

- **AC-1** ssh-manager allow 条目已移除：
  `uv run python -c "import json;a=json.load(open('.claude/settings.json'))['permissions']['allow'];assert 'mcp__ssh-manager__*' not in a, a;print('ssh-manager removed from allow')"` → exit 0
- **AC-2** allow 条数 24→23：
  `uv run python -c "import json;a=json.load(open('.claude/settings.json'))['permissions']['allow'];assert len(a)==23, len(a);print('allow =',len(a))"` → exit 0 且打印 `allow = 23`
  （**须 `uv run python`**——本机裸 `python` 不在 PATH，仓惯例见 CLAUDE.md Commands 段；单命令同时自证 JSON 合法 + 条数）
- **AC-3** deny 未误动（A 口径）：
  `uv run python -c "import json;d=json.load(open('.claude/settings.json'))['permissions']['deny'];assert len(d)==9, len(d);print('deny =',len(d))"` → `deny = 9`
- **AC-4** 未误伤其他 allow 面（biz/memory/github/serena/playwright 计数不变）：
  `grep -cE '"mcp__(pg-mj-|github|serena|playwright)' .claude/settings.json` → **11**（memory×5 + biz×3 + github + serena + playwright；ssh 已移除，其余不动）
- **AC-5** 零自动依赖不变量（PR 内重跑，不承袭 Intake）：
  `grep -rn "mcp__ssh-manager__ssh_\|ssh_execute_sudo(\|ssh_deploy(\|ssh_db_import(" .claude/skills/ .claude/scripts/ scripts/ src/ | wc -l` → `0`
- **AC-6** 收窄方向自证（无 widening）：diff 仅**删除** allow 行（A）/ 删 allow + **增 deny**（C）——`git diff` 无任何 allow 面新增（`+ "mcp__...` 在 allow 段）
- **AC-7** 四 gate 脚本本地全绿（V8/V9/V10/V11 各 exit 0，预期零变化——无 `.py` 读 settings.json）
- **AC-8** `pytest tests/unit tests/eval` 全绿（clean worktree 无 #298 假红）；`ruff check` + `mypy src/mj_agent` 干净
- **AC-9** `check_frontmatter.py` + `check_wikilinks.py` exit 0
- **AC-10** CI 全绿（本切片不改任何 gate 姿态）
- **AC-11** merge 后：本 2 文件 flip `completed` + #312 议题 2「ssh-manager wrapper 方案」复选框勾选

### 8.1 Gate 5 若选 B / C 的 AC delta

- **选 C**：AC-2 allow=23 不变；**AC-3 改** deny=9→**23**（+14），且断言 14 个 destructive 名逐一在 deny；
  新增 **AC-3b** `uv run python` 断言 deny 含 `mcp__ssh-manager__ssh_execute_sudo` 等 14 名。
- **选 B**：AC-1 改为「通配移除但 read 子集 per-tool 在 allow」；AC-2 allow=23+read子集数；需列白名单精确集。
  （**不推荐**，§5.1）

## 9 Verification

- **Level A（read-only）**：`ruff check` · `mypy src/mj_agent` · `pytest tests/unit tests/eval`（clean worktree 无 #298 假红）·
  `check_frontmatter.py` · `check_wikilinks.py`
- **Level A（gate 四件）**：`check_development_agent.py --all`（V8）· `check_agents_projection.py --all`（V9）·
  `agents_sync.py --check --surface skills`（V10）· `--surface mcp`（V11）
  > **预期零变化**：无 `.py` 读 `.claude/settings.json`（Intake §5 实测——`grep -rln "settings\.json" scripts/ .github/ tests/ --include=*.py` = 0）→ 四 gate 对本 diff 不可见。**PR 内仍复跑**，不承袭。
- **Level A（自证 grep）**：§8 AC-1 ~ AC-11——AC-5 在 PR 内重跑「零自动依赖」不变量
- **Level B**：无（不跑 side-effect；不改 CI、不翻 gate、不动容器）
- 唯一 CI 侧接触面：`.github/workflows/check-stale-docs.yml` path-filter 含 `.claude/**` → 跑 `find_stale_docs.py`；
  仅 rename/delete 面、恒 exit 0、`continue-on-error: true` → 不会红。
- **大闭幕后**：全 diff credential 扫描（settings 改动不含凭据，但按纪律扫一遍）+ doc 冗余体核对
  （本切片不改 contract/INDEX，无冗余体）。

## 10 Risks / Anti-goals

| 风险 | 缓解 |
|---|---|
| **误伤其他 allow 面** | AC-4 grep 硬证 11 条非 ssh MCP 面不变；AC-2 allow=23 |
| **A 口径在 bypass 模式无 hard floor** | 已如实呈 §5（A vs C 权衡）；若 Owner 重此点则拍 C。仓安全模型本就假定交互模式（5 必停「仅交互模式成立」） |
| **C 口径 deny-list 维护/选择判断** | §5.2 拟定 14 条 destructive 子集有据（§3.B 最高危 13 + key_manage）；最终集 Gate 5 拍板定，落 plan |
| **把 vault Option B（含删 ssh 通配）当作本切片 verbatim** | Intake §2：vault §四 已把 ssh 面递延本 issue「一次拍板」；本切片是那次拍板 |
| **scope drift 到 .mcp.json / proxy / user-config** | §6 Out-of-scope 逐项有据；AC 不触这些面 |
| **将来手动 ssh 被意外挡（C）** | ssh-manager 仍 enabled、可显式批准（A/B）；C 下 destructive 需改 settings——已在 §5 代价栏明示 |

**Anti-goals**：不放宽任何权限面；不动 4 必停；不翻 gate 姿态；不改 `.mcp.json`/manifest/`.agents`/`.codex`；
不重写任何 `state: completed` 的前序切片记录。

## 11 Owner Gates

| Gate | 触发点 |
|---|---|
| **Stage 5** | 本 Plan 拍板 **+ 收窄口径 A/B/C 选定**（进 Stage 8 实施前） |
| protected-path prompt | W1 写 `.claude/settings.json`（harness 硬编码，`allow` 不可抑制） |
| Stage 13 | commit / push / PR 创建 **各单独拍板** |
| merge | **交 Owner**（classifier 拦 agent 直合 develop） |
| **A13 适用** | settings allowlist diff 走 PR 合并审查 |
| **不触发** | `ci-blocking-gate-toggle`（不改 gate 姿态）· A14（不动 `.mcp.json`）· D-017（不动 manifest/`.agents`/`.codex`） |

## 12 Next Step

**Gate 5 拍板收窄口径 A/B/C**（AskUserQuestion）→ Stage 8 实施（W1-W3，按拍板口径）→ Stage 10/11 验证 + 自评
（含 5-lens 对抗审查 + 全 diff credential 扫描）→ Gate 13 PR → 交 Owner 合并 → Stage 17 post-merge
（state flip PR + #312 议题 2 勾选 + 分支 origin/gitee 双清 + worktree remove + `closingIssuesReferences` 核验，
本仓 Closes 恒不生效 → issue 手动关）。
