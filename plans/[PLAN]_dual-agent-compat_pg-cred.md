---
type: plan
slug: dual-agent-compat-pg-cred
summary: dual-agent-compat v5 pg-credential 单一真相 + memory×5 Codex 投影执行计划（议题 3 + 议题 1 合并）——.mcp.json 10 个 pg server 的 args 由 ${VAR:-default} 改 literal var-NAME（过 G-A/G-B）+ env 由 {} 改 {NAME:${NAME}}（过 _ENV_REF 纯度→emit env_vars=[NAME]）；pg-server-start.cmd 加 name→env→URL 解析 + 显式失败（env 未设=硬失败，call set 变体防 !/% 破坏）；manifest memory×5 project-with-adr→project（D-017）；agents_sync sync 重生 .codex/config.toml + .agents/** + lock；单一真相 = secrets-mcp.enc→HKCU env；biz×5+ssh 永 never（ADR-006/009）不变；逐门独立拍板（protected path→A14→D-017→sync→V11）；1 PR，maintain/353-pg-cred-single-source；触 A14+D-017+protected path；总锚 #312
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-17
state: active
version: 1.0
track: shared
related_adrs:
  - decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md
  - decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md
  - decisions/ADR-006_Fail_Safe_Reads.md
---

# [PLAN] 双工具兼容 v5 — pg-credential 单一真相 + memory×5 投影（issue #353）

## 1 Linked Artifacts

- Issue：**#353**（本切片）；总锚 **#312**（议题 3 pg-default + 议题 1 memory×5 promotion 复选框）。
- 上游计划：[[[PLAN]_dual-agent-compat|v5 计划]] §S3（L315 议题 1）+ L234/L539（D-013 三档）+ L521/L522
  （三议题 + D-017 邻接面）。
- ADR：[[decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] D-013（MCP 三档）/ D-017
  （A14 anchor 覆盖派生面）· [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]]（MCP secret 走
  `secrets-mcp.enc`→HKCU env，永不入 .env）· [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]/ADR-009
  （数据边界；biz×5 永 never）。
- 同批 [[[INTAKE]_dual-agent-compat_pg-cred|INTAKE]]（锚/方案拍板 + Stage 0 核查 + Spike 结果）。
- Owner vault 备料 `[ASSESSMENT]_pg-credential-default-single-source-2026-07-16.md`（不入仓，承 S2 #330 AC10）。

## 2 Context

**「pg 凭据 default 单一真相」的实体**：同一连接串语义今有两处来源——权威源 `secrets-mcp.enc`→HKCU env
（ADR-030），与 `.mcp.json` 内嵌字面 `${VAR:-default}`——且 5 条 memory 形态不一致（3 有 default / 2 裸引用），
无治理记录，疑历史遗留。第二处真相中 3 条含 credential 形状字面量（1 条真实本地口令）。

**为何合并议题 1**：memory×5（`project-with-adr`）投影进 `.codex/config.toml` 供 Codex 消费一经开启即被
两道 fail-close guard 挡死（G-A `${` 子串 / G-B userinfo 形状，`agents_sync.py:273`/`:279`），而解开它们
正是议题 3 的内容。脱离议题 1 单做议题 3 无收益却付 A14 代价 → 二者是同一决策的两半（vault §五）。

**边界不变式**：biz×5 + ssh-manager 对 Codex 永 `never`（ADR-006/009 数据边界；直投 = 把绕 L1/L1b 的
raw client 递给无 harness 门的工具）。memory pg 是 mj-agent **自有** memory / checkpointer 存储（独立库 +
独立凭据 `mj_agent_memory_user`）→ 可投影，凭据仍 by-name-only、零字面。**注（5-lens 更正）**：memory
checkpoint **确含 execute_sql 的 biz 派生行**（无摘要，Phase 2+），但读它无法触达 biz 表 / 绕 L1/L1b、
只得历史已批准结果、Claude 已同径（extends 非 creates）——投影安全性据此，非「无 biz 数据」（详 ADR-037 理据 1 / §13 C1）。

## 3 Scope

- **In-scope**（1 PR，逐门独立拍板）：
  1. `.claude/scripts/pg-server-start.cmd`：加 name→env→URL 解析 + 显式失败语义（服务全 10 个 pg server）。
  2. `.mcp.json`：全 10 个 pg server 的 `args` `${VAR:-default}`→literal var-NAME + `env` `{}`→`{NAME:"${NAME}"}`（**原子**）。
  3. `sdd/development-agent.yml`：`mcp.servers` memory×5 `project-with-adr`→`project`。
  4. `agents_sync.py sync`：重生 `.codex/config.toml` + `.agents/**` + `.agents.lock.json`（源+产物+lock 同 commit）。
  5. memory×5 投影 ADR（若 Owner 采 ADR 路径，§10 门 3）。
  6. `docs/guide/[GUIDE]_Developer_Onboarding.md`（若移除零配置 default，§5）。
  7. 本 `[INTAKE]+[PLAN]` 对。
  8. `capabilities/infrastructure/mcp-server-governance/contracts/mcp-server.contract.yml`（10 个 pg 的 `credential_mode` → `wrapped_script_env_name_resolution` + `default_url*` 全 null；#353 使其 stale，`freeze_anchor=.mcp.json`）+ `docs/INDEX.md`（ADR-037 登记）——**self-review 发现**。
- **Out-of-scope**（各自独立，不在本 PR）：议题 2（ssh-manager wrapper）· P4 本体 / S3 skills-gate blocking ·
  任何 `ci.yml` gate 姿态变更 · biz×5 / ssh 的投影档变更（永 `never`）· 4 项 in-source 专属必停面 ·
  `agents_sync.py` 投影**逻辑**改写（本切片预期只跑 `sync`，不改 emitter；若 Stage 8 发现须改则单独标 D-017 门）。

> **纵切片归属**：本切片是议题 3+1 的自身可验、可独立 review-合的窄完整路径（传名 + 投影解闸）。
> 议题 2 / P4 / S3 余项 `blocked-by` 各自拍板或观察窗口，另行成片。

## 4 Design

### 4.1 传名形态（核心）

每个 pg server（先 memory×5，因原子性同批改 biz×5）由：

```jsonc
// BEFORE（memory-dev，.mcp.json:22-30）
"args": ["/c", ".claude\\scripts\\pg-server-start.cmd",
         "${MJ_AGENT_PG_MEMORY_DEV_URL:-postgresql://mj_agent_app:<dev-throwaway-pw>@localhost:5433/mj_agent_memory}"],
"env": {}
// AFTER
"args": ["/c", ".claude\\scripts\\pg-server-start.cmd", "MJ_AGENT_PG_MEMORY_DEV_URL"],
"env": { "MJ_AGENT_PG_MEMORY_DEV_URL": "${MJ_AGENT_PG_MEMORY_DEV_URL}" }
```

- `args` 末位 = **literal 变量名**（无 `${` → 过 G-A `:273`；无 userinfo 形状 → 过 G-B `:279`）。
- `env` = **纯 `${VAR}` 引用**（过 `_ENV_REF` 纯度 `:290` → emit `env_vars=["MJ_AGENT_PG_MEMORY_DEV_URL"]`）。
- **Claude 侧**（`.mcp.json`）：harness 把 `${MJ_AGENT_PG_MEMORY_DEV_URL}` 插值进子进程 env；arg 传字面名；
  `pg-server-start.cmd` 从 env 按名解析出 URL。
- **Codex 侧**（`.codex/config.toml`，`sync` 生成）：`args=[…, "MJ_AGENT_PG_MEMORY_DEV_URL"]` +
  `env_vars=["MJ_AGENT_PG_MEMORY_DEV_URL"]`；Codex 按名从父 HKCU env 透传该变量给子进程；同一脚本解析。
  **零字面凭据入 `.codex/config.toml`**（G7 + PJ044 守）。

### 4.2 pg-server-start.cmd 解析（Spike 1/1b/1c 已定稿）

脚本 `:2` 有 `setlocal enabledelayedexpansion`（cache-retry 依赖）。**关键发现**（Spike 1b）：
`call set "URL=%%%NAME%%%"` 在延迟展开下对**百分号编码 `%NN` 安全**（Case B `%40` 保真），但对
**裸 `!`** 会被吃掉（Case C `pa!ss@…` → `pa5433`）。**定稿设计 = nested `disabledelayedexpansion`**
（初版 endlocal-drop 只在 caller `/V:OFF`〔默认〕成立；5-lens correctness 逮到 `/V:ON` 下裸 `!` 仍被吃，
Spike 1d 证 nested-disabled 在 `/V:ON`|`/V:OFF` 均保真、**无条件**）：缺 arg 在 discovery 前 fail-fast；
discovery 段（需 `!VAR!`）后**嵌套**一个 disabled 作用域再解析 URL（NODE_PATH + parent env 继承入嵌套域）：

```bat
if "%~1"=="" ( echo [pg-server] ERROR: missing connection variable name 1>&2 & exit /b 2 )   REM discovery 前
:DISCOVER
REM ... 既有 npx 发现 + cache-retry（用 !VAR!）... 设 NODE_PATH ...
setlocal disabledelayedexpansion              REM 嵌套 disabled：裸 ! 无条件免疫；NODE_PATH+parent env 继承
set "PG_CONN_NAME=%~1"
call set "PG_CONN_URL=%%%PG_CONN_NAME%%%"      REM 延迟展开 OFF → 裸 ! 免疫、%NN 保真
if not defined PG_CONN_URL ( echo [pg-server] ERROR: env var %PG_CONN_NAME% is not set 1>&2 & exit /b 3 )
node "%~dp0pg-server-wrapper.mjs" "%PG_CONN_URL%"
```

- **显式失败**（env 未设 = exit 3；缺 arg = exit 2）取代今日 `:-default` 静默兜底 = §5 tightening。
- **wrapper 契约不变**：URL 仍落 argv[2]（`pg-server-wrapper.mjs` 不解析 argv，转发解析后 URL 即可）。
- **URL 建议百分号编码**（RFC 3986；`!`→`%21` 等）；但 nested-disabled 是**无条件** defense——即使漏编码裸 `!`
  也保真（不依赖 caller `/V` 默认）。Spike 1b/1c/1d 证据见 [[[INTAKE]_dual-agent-compat_pg-cred|INTAKE]] §3.1。
- **10-server 原子性**：脚本契约由「收 URL」变「收变量名」→ biz×5 的 `.mcp.json` args 必须同批改名
  （否则 biz×5 传 `${...}` 给按名解析脚本 → 静默错连）。这是本切片最大隐藏成本 + 最大风险点。

### 4.3 manifest flip + emitter 行为

`sdd/development-agent.yml:731-735` memory×5 `project-with-adr`→`project`。翻转后：
- `check_agents_projection.py:137` `load_mcp_projection` 收 memory×5 入 `project_servers`。
- `agents_sync.py` emitter 遍历 project 档 → 逐一过 `:255-297` fail-close 链（unknown field / type=stdio /
  command / args list / **G-A** / **G-B** / **env 纯度**）→ 渲染 `[mcp_servers.pg-mj-agent-memory-*]` +
  `env_vars`。§4.1 形态保证全过。
- `check_codex_config`（PJ040-045）：`expected = project 集`（含 memory×5）；PJ044 守 never 档不泄漏
  （biz×5+ssh 仍 never，不得现身）；lock 保留路径形键。

### 4.4 Spike 2（env_vars 继承）

- **2a = precedent-proven**：`.codex/config.toml:19` github `env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"]`
  （HKCU secret）+ #330 AC7 实机成功；memory×5 机制逐字相同；file header L5-8 载明机制。
- **2b = 实施期实机核验**（Owner 协同）：真投影后 `codex mcp list` 见 5 个 memory 档 + 一 memory-server 查询
  成功（Codex→pg-server-start.cmd 解析名→连库）。由 Spike 1 + 2a 两已证半环组成，残余风险低。

## 5 收窄的真实影响（不夸大、不缩小）

- **加**：memory×5 对 Codex 可用（能力面对等）；单一真相（消 `.mcp.json` 第二处 default）；零字面凭据。
- **收紧**：env 未设 = 显式失败（非静默 `:-default` 兜底）——更安全，但改新 dev 零配置体验（须 Owner 接受 + onboarding 同步）。
- **不动**：运行期 `src/mj_agent/**` 零改 · biz×5+ssh 永 never（ADR-006/009）· 4 必停面 · CI gate 姿态 ·
  `.env`/secrets（不解密、不写）· `agents_sync.py` 投影**逻辑**（只跑 sync，不改 emitter）。
- 唯一新行为面 = pg-server-start.cmd 收变量名（非 URL）+ 5 memory server 现身 `.codex/config.toml`。

## 6 Work Breakdown（1 PR，`maintain/353-pg-cred-single-source`；逐门独立拍板，不合并）

| # | 门 | 文件 | 改动 | 门类型 |
| --- | --- | --- | --- | --- |
| G0 | — | （Spike）| Spike 1 定稿（`!VAR!` vs `call set`，特殊字符口令用例）；Spike 2b 计划 | — |
| W1 | protected path | `.claude/scripts/pg-server-start.cmd` | name→env→URL 解析 + 显式失败（§4.2） | `.claude/**` 权限 prompt |
| W2 | **A14** | `.mcp.json` | 10 个 pg server args→名 + env→`{NAME:${NAME}}`（原子，§4.1） | A14 硬停 |
| W3 | **D-017** | `sdd/development-agent.yml` | memory×5 `project-with-adr`→`project`（§4.3） | D-017 |
| W4 | **D-017 邻接** | `.codex/config.toml` + `.agents/**` + `.agents.lock.json` | `agents_sync.py sync` 重生（源+产物+lock 同 commit） | D-017 邻接 |
| W5 | 决策 | `decisions/ADR-0XX`（Owner 2026-07-17 拍板=采） | memory×5 投影 ADR（memory≠biz；§10 门 3'） | ADR HITL |
| W6 | 条件 | `docs/guide/[GUIDE]_Developer_Onboarding.md` | 零配置 default 移除同步（§5） | docs |
| W7 | — | 本 `[INTAKE]+[PLAN]` 对 | state: active | — |
| W8 | 文档一致 | `mcp-server.contract.yml` + `docs/INDEX.md` | contract `credential_mode`/`default_url` 随 #353 更新〔freeze_anchor=.mcp.json〕（**self-review 发现**）+ INDEX 登记 ADR-037 | docs |

**红→绿 commit 序建议**：W1（脚本 + Spike 定稿）→ W2（.mcp.json，本机起 10 server 验）→ W3（manifest）→
W4（sync，V11 复核）→ W5/W6/W7（ADR/onboarding/plan）。每门 Owner 拍板后落盘。

## 7 Verification

- `uv run python scripts/sdd/agents_sync.py --check --surface mcp`（V11 blocking）+ `--surface skills`（V10）
- `uv run python scripts/sdd/check_agents_projection.py`（V9）· `check_development_agent.py`（V8）
- `uv run pytest tests/unit tests/eval`（含既有 canary/V8/V9 测试全过）· `uv run ruff check` · `uv run mypy src/mj_agent`
- **本机 Level B**：`agents_sync.py sync` 后 `git diff` 只动预期产物；Claude 侧起 10 个 pg server（memory+biz）全成；
  实机 Codex `codex mcp list` 见 memory×5 + 一查询成功（Spike 2b，Owner 协同）。
- **negative test**：env 未设 → server 显式失败（exit 3，非静默连错库）；`.codex/config.toml` 零 credential
  （`grep -iE "postgresql://|:.*@|password" .codex/config.toml` = 0 命中）。
- 结构性防呆：本机带 `.env` 跑 unit 有 [[project_prod_repoint_local_env|#298]] 2 假红，clean worktree 不受影响。

## 8 验收标准（全部可执行自证；承 [[feedback_wrong_premise_voids_decision|#341/#344]]「AC 逮住作者本人」教训；精确 pattern PR 前单独跑一遍）

- [ ] **AC-1**（args 无内嵌 default）：`grep -cE '\$\{[A-Z_]+:-' .mcp.json` = **0**〔无 `${VAR:-default}` 内嵌 default 语法；改后 args 末位是裸变量名〕。注：`.mcp.json` 仍有 github/ssh/pg 的**合法** env `${VAR}` 纯引用——故校 args 无 default 用此精确 pattern，非「全文件 ${ = 0」（原松断言会假失败，5-lens 2026-07-17 已消除）。
- [ ] **AC-2**（env_vars 投影）：`.codex/config.toml` 含 `[mcp_servers.pg-mj-agent-memory-dev]` 且其 `env_vars` 含 `"MJ_AGENT_PG_MEMORY_DEV_URL"`（5 个 memory 各一）。
- [ ] **AC-3**（零字面凭据，G7/PJ044 核心）：`grep -icE "postgresql://|[a-z0-9_]+:[^@ ]+@|password|replace_with|local-dev-only" .codex/config.toml` = **0**。
- [ ] **AC-4**（never 不泄漏）：`.codex/config.toml` **无** `pg-mj-system-biz-*` / `ssh-manager` 任一 `[mcp_servers.*]`；V9 `check_agents_projection.py` 退出 0（PJ044 无触发）。
- [ ] **AC-5**（显式失败 tightening）：Spike/测试证 env 未设 → `pg-server-start.cmd` exit 3；缺 arg → exit 2（不静默 `:-default`）。
- [ ] **AC-6**（V 全绿）：`agents_sync.py --check --surface mcp`（V11）+ `--surface skills`（V10）+ `check_agents_projection.py`（V9）+ `check_development_agent.py`（V8）全退出 0。
- [ ] **AC-7**（回归）：`uv run pytest tests/unit tests/eval` 全绿 · `uv run ruff check` 无违规 · `uv run mypy src/mj_agent` 通过。
- [ ] **AC-8**（source+产物+lock 一致）：`agents_sync.py --check --surface mcp` 证 `.codex/config.toml` 与 manifest+`.mcp.json` 同步、lock 键匹配（无 drift）。
- [ ] **AC-9**（10-server 原子）：`.mcp.json` 10 个 pg server args 末位**均**为 literal 变量名——`grep -cE '^ +"MJ_AGENT_PG_(MEMORY|BIZ)_[A-Z_]+_URL"$' .mcp.json` = **10**〔锚定行首缩进 + 行尾引号，排除 env-key 行 `"…_URL":`〕。（5-lens 对抗审查 2026-07-17 逮到原松 pattern `'MJ_AGENT_PG_.*_URL"'` 命中 **20**〔含 10 env-key 行〕= 假失败——AC 逮住作者本人，已锚定修正。）
- [ ] **AC-10**（Spike 2b，Owner 协同）：实机 Codex `codex mcp list` 列 memory×5；一 memory-server 查询成功（凭据经 env_vars 名链）。

> **§注（AC-1/AC-9 精确性，5-lens 2026-07-17 定稿）**：改后 `.mcp.json` 仍有 github env、ssh-manager
> env ×7、以及新加的 10 个 pg env `{NAME:"${NAME}"}` 值——这些是**合法** `${VAR}` 纯引用。故 AC-1 校「无
> 内嵌 default」用 `${VAR:-` pattern（=0）、AC-9 校「args 是裸名」用行锚定 pattern（=10），均已 PR 前实跑。
> 原松 pattern（AC-1 全文件 `${`=20、AC-9 `.*_URL"`=20）会假失败，5-lens 逮到已消除。

## 9 Risks / Anti-goals

- **10-server 非原子**（biz×5 漏改 → 静默错连）：mitigate = W2 一次改全 10 + AC-9 计数 + 本机起全 10 验。
- **口令特殊字符**（裸 `!`/`%`/`&`/`=` 破坏解析或转发）：mitigate = **nested `disabledelayedexpansion`**（Spike 1d 证 /V:ON 下裸 `!` 亦保真，**无条件**，不依赖 caller 默认）+ `call set` 名解引用（`%NN` percent-encode 保真）+ 转发用 `"%PG_CONN_URL%"` 引号 + 头注建议 RFC 3986 percent-encode。
- **字面凭据泄漏进 `.codex/config.toml`**：mitigate = §4.1 形态（env by-name）+ emitter G-A/G-B/纯度守 + AC-3 + G7 + PJ044。
- **D-017 语义变更**：本切片 memory×5 档翻转 = **真** trust-posture 变更（非 surface-match）→ 逐门 Owner 拍板；
  `agents_sync.py` 只跑 `sync` 不改逻辑（若须改则另标 D-017 逻辑门）。
- **Anti-goal**：不碰 biz×5/ssh 投影档（永 never）· 不改 emitter 投影逻辑 · 不放宽任何 gate · 不解密/写 secret ·
  不删既有测试。

## 10 Owner Gates

- **已拍**（[[[INTAKE]_dual-agent-compat_pg-cred|INTAKE]] §7）：切片锚 B + 议题 3 方案 A。
- **逐门待拍**（各自 `OWNER_APPROVAL_REQUIRED`，不合并）：
  1. **W1 protected path**（`.claude/scripts/pg-server-start.cmd`，`.claude/**` 权限 prompt）。
  2. **W2 A14**（`.mcp.json` server inventory + credential mode，`mcp-server-trust-posture-change`）。
  3. **W3+W4 D-017**（manifest `mcp.servers` memory×5 档翻转 = 真 trust-posture 变更；派生 `.codex/config.toml`+`.agents/**` 重生；`policies/ai-agent.md:94` + ADR-036 D-017；**非 harness 保护路径**，由 Owner 拍板 + V8/V9/V11 + merge review 兜底）。
  3'. **ADR 决策 = 单开 ADR**（Owner 2026-07-17 拍板）：memory×5 投影 ADR（`project-with-adr` 的 ADR 半边，论证 memory≠biz 投影安全）。
  4. **tightening = 接受**（Owner 2026-07-17 拍板）：env 未设 = 显式失败（无 default）+ onboarding 同步（§5）。
  5. **Spike 2b**：实施期实机核验（推荐）vs 现在跑合成 Spike。
  6. **commit / push / PR 创建 / merge**（合入 develop 交 Owner，classifier 硬拦 agent 直合）。
- **§3.1 专属 4 必停**：**无**触发（不动 skills/system.md/qcm_catalog/SQL guardrail）。
- **`.env`/secrets**：只读、不解密、不写（ADR-030；MCP secret 走 `secrets-mcp.enc`→HKCU，永不入 .env）。

## 11 Next Step

Stage 5 Plan HITL Gate（§10 待拍门，Owner 逐一拍）→ Stage 8 实施（`/mj-agent-flow-implement`：G0 Spike 定稿
→ W1→W7 红→绿，逐门拍板落盘）→ Stage 10 verify（V8/V9/V11 + negative + 本机起全 10 + 全套件）→ Stage 11
self-review（5-lens 对抗审查 workflow）→ commit/push/PR 交 Owner → merge 后 flip PR 翻 state completed +
手动 `gh issue close #353`（Closes #N 本仓恒不生效，base=develop≠默认分支）。

## 12 交办 / pre-existing drift（本切片登记，不在 #353 scope 内）

- **docs/INDEX.md ADR 表 drift**：该表意在列 active（非 archived）ADR，但 **ADR-031 / 032 / 035 / 036
  未入表**（pre-existing，非本切片造成）。本切片只登记 ADR-037（自身交付物）；035/036（dual-agent 同族）
  与 031/032（SDD refactor / skill schema monitoring）留后续 index-reconciliation，另开 documentation 小 PR。
- **Spike 2b / AC-10**：Codex 实机 `codex mcp list` + memory-server 查询 = 实施期实机核验，Owner 协同
  （D-015 trust 每工程师×每 worktree 人工；[[reference_codex_headless_windows_invocation|Codex headless 四坑]]）。
- **`.cmd` 无自动化测试**（5-lens atomicity 逮，判 not-real）：`pg-server-start.cmd` 的传名解析 + exit 2/3
  只由 Spike 1/1b/1c/1d 手验 + AC-5 记录，CI（ubuntu）不跑 Windows `.cmd`。留后续：可加 `os.name=='nt'`
  skip 的 pytest subprocess 测（本机跑、CI skip），或维持现状（spike 命令 + 期望退出码入本 plan）。

## 13 5-lens 对抗审查处置（2026-07-17，workflow `w7d0654bv`：3 confirmed / 3 refuted）

| # | lens | severity | 处置 |
| --- | --- | --- | --- |
| C1 | security + honesty | med/high | **ADR-037 前提「memory 不含 biz 数据」= 假**——checkpointer 持久化 `execute_sql` ToolMessage（envelope 含 biz `rows`/`business_summary`）、当前无摘要（Phase 2+）→ memory 库**确含 biz 派生行**。已更正 ADR 理据 1 + Consequences 为诚实前提（独立库 + 独立凭据 `mj_agent_memory_user` → 无法触达 biz 表 / 绕 L1/L1b、只得历史已批准结果；Claude 已同径 → extends 非 creates；双门 gated；AGENTS.md 自守）。**动作面不变但风险表述实变 → 已带更正回 Owner，Owner 2026-07-17 在更正前提下重确认投影决策成立**（承 [[feedback_wrong_premise_voids_decision|错误前提纪律]]）。 |
| C2 | governance | med | **AC-9 pattern 假失败**（`'MJ_AGENT_PG_.*_URL"'` 命中 20 非 10，含 env-key 行）——已锚定为 `^ +"…_URL"$`=10；AC-1 同期定稿（`${VAR:-`=0）。 |
| R1 | correctness | low | 裸 `!` 在 caller `/V:ON` 下破坏（refuted：非默认 OS 设置 + 违反 percent-encode 契约）——**仍主动硬化**为 nested-disabled（Spike 1d 无条件保真），§4.2。 |
| R2 | atomicity | low | `.cmd` 无自动化测试（refuted：hypothetical future-edit）——登记 §12 follow-up。 |
| R3 | governance | low | AC-1 全文件 `${`=0 自相矛盾（refuted：自带 §注 self-defuse）——仍定稿为精确 pattern。 |

> 诚实说明：C1 是本切片最重要的发现——自验（V8/V9/V11 + 700 tests）全绿仍漏掉「checkpoint 含 biz 派生行」
> 这一事实层前提错误，由 5-lens security+honesty 双 lens 独立逮到。**Owner 已于 2026-07-17 在更正前提下重确认投影决策成立 → 可 commit。**
