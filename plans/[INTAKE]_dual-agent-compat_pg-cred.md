---
type: intake
summary: 双工具兼容 v5 第十二执行切片（#312 议题 3 pg-credential 单一真相 + 议题 1 memory×5 Codex 投影，合并为一次决策）的 Stage 0 Intake 落盘——.mcp.json 10 个 pg server 由内嵌 ${VAR:-default} 改传名（literal var-NAME）+ pg-server-start.cmd 加 name→env 解析与显式失败语义 + manifest memory×5 project-with-adr→project（D-017）+ agents_sync sync 重生 .codex/.agents/lock；单一真相 = secrets-mcp.enc→HKCU env；触 A14（.mcp.json）+ D-017（manifest mcp/agents_sync/.codex/.agents）+ protected path（.claude/scripts）；maintain/High/1 PR；对应 issue #353（总锚 #312）；Owner 2026-07-17 拍板 A（传名 + merge 议题1），选自候选 B(pg-default)/A(A6)/E(ssh-wrapper)/Hold
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-17
completed: 2026-07-17
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — pg-credential 单一真相 + memory×5 投影（issue #353）

> Stage 0 输出于 2026-07-17 会话内产生并当日落盘（worktree `maintain/353-pg-cred-single-source`
> 内，保 develop 干净）；触发 §2.1 落盘判定（High 风险 + 多面〔.mcp.json / scripts / manifest /
> agents_sync / 派生产物〕 + HITL 点 ≥ 3〔A14 + D-017 + protected path + commit/push/PR + tightening
> 接受 + ADR 决策〕 + 家族 `[INTAKE]_+[PLAN]_` 成对惯例 + 多迭代〔spike → 逐门〕）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §S3（L315 议题 1）+ L234/L539（D-013 三档；memory×5
> = `project-with-adr` 独立拍板后落地）+ L521/L522（三议题 + D-017 邻接面）+
> [[decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] D-013/D-017 +
> [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]]（2-bundle secrets）+ 总锚 #312（议题 1 + 议题 3）+
> Owner vault 备料 `[ASSESSMENT]_pg-credential-default-single-source-2026-07-16.md`（不入仓）。

## 1 Task Classification

- **Type**：`maintain`（`.mcp.json` + `.claude/scripts/` + manifest + `scripts/sdd/agents_sync.py`
  投影生成器；分支前缀 `maintain/`，承 S1 `maintain/326-…` / S2 `maintain/330-…` / S3a
  `maintain/350-…` 先例）。**无 `src/mj_agent/**` 运行期改动**。
- **Base branch**：`develop` → PR base `develop`。
- **估计影响范围**：
  - `.claude/scripts/pg-server-start.cmd`（加 name→env 解析 + 显式失败；服务全 10 个 pg server）— **protected path**
  - `.mcp.json`（10 个 pg server 的 `args` + `env` 原子改）— **A14 硬停**
  - `sdd/development-agent.yml`（`mcp.servers` memory×5 `project-with-adr` → `project`）— **D-017**
  - `scripts/sdd/agents_sync.py`（**预期只读跑 sync；若需改逻辑则触 D-017**——见 §4）
  - 派生 `.codex/config.toml` + `.agents/**` + `.agents.lock.json`（`sync` 重生，**不手改**）— **D-017 邻接**
  - `decisions/ADR-0XX`（memory×5 投影 ADR，若 Owner 采 ADR 路径——见 §6/§7）
  - `docs/guide/[GUIDE]_Developer_Onboarding.md`（若移除零配置 dev default——见 §5 tightening）
  - 本 `[INTAKE]+[PLAN]` 对
  - **不写 / 只读**：`config/secrets*.enc`（doctor 不自解密）· `.env`（MCP secret 永不入 .env，ADR-030）·
    4 项 in-source 专属必停面（guardrail/precheck/system.md/qcm_catalog）· biz×5 + ssh-manager 投影档（永 `never`）

## 2 锚选定（Step 1）

Owner 2026-07-17 AskUserQuestion 两级拍板：
1. **切片锚 = B（pg-default）**——从候选 B（pg-default）/ A（A6 durability gate）/ E（ssh-manager
   wrapper）/ Hold 中选。理由：vault 评估已备料、最 ready 的决策腿、且 unblocks 议题 1（memory×5
   硬依赖议题 3）。D（P4 本体 + S3 skills-gate blocking）结构性出局（日历腿 2026-07-28 才绑定，§11.1 AND）。
2. **议题 3 方案 = A（传名 + merge 议题 1）**——从 A（传名）/ B（不投影，关议题 1）/ C（emitter 侧字面转换，
   设计上排除）中选。承 vault 评估 §五「A 须与议题 1 合并为一次拍板」（二者是同一决策的两半）。

## 3 Stage 0 核查产出——对 brief / vault 评估的确认与更正

> 全部事实断言采于 **develop @ `f486999`**（本切片 base）+ worktree
> `maintain/353-pg-cred-single-source`（G1 新建，2026-07-17 实读）。

| # | 断言（brief / #312 / vault） | 核查结果 | 证据（fresh, develop @ f486999） |
| --- | --- | --- | --- |
| 1 | #312 议题 3「传名 vs Codex 侧强制显式 env」是对称两选项 | **证伪 → 更正** | 「显式 env」只去 `:-default`（过 G-B），args 仍是裸 `${VAR}` → G-A `if "${" in arg` 无条件触发（`.mcp.json:45`/`:63` 裸引用即例证）；唯一可行 = 传名。带回 Owner，Owner 拍 A（承 [[feedback_wrong_premise_voids_decision|错误前提纪律]]） |
| 2 | vault 评估记 guard 在 `agents_sync.py:262-268`（G-A）/ `:269-273`（G-B） | **行号漂移**（S3a #350 后 +~11 行）；机制不变 | 实读：G-A `if "${" in arg` = `agents_sync.py:273`；G-B `_ARG_USERINFO.search` = `:279`；env 纯度 `_ENV_REF` = `:290` |
| 3 | memory×5 现 `project-with-adr` = 投影 dormant（promotion 闸，非活故障） | **确认为真** | `check_agents_projection.py:137` `if policy == "project":` 只收 project 档；`project-with-adr` 落 neither → 不投影、不 never-泄漏校验；`sdd/development-agent.yml:731-735` memory×5 逐行 `project-with-adr` |
| 4 | 10 个 pg server 共用 `pg-server-start.cmd`，脚本原样转发不解析 default | **确认为真** | `.mcp.json` 10 处 `.claude\scripts\pg-server-start.cmd`；`pg-server-start.cmd:66` `node "%~dp0pg-server-wrapper.mjs" %*`（原样转发）；`pg-server-wrapper.mjs` 全 53 行无 `process.argv`/`process.env`（URL 必落 argv[2]） |
| 5 | 5 条 memory args 形态不一致（3 有 default / 2 裸引用） | **确认为真** | `.mcp.json`：dev `:27` / test-lan `:36` / prod-lan `:54` 内嵌 `${…:-postgresql://…}`（其中 dev 那条内嵌一条本地 throwaway 口令，自述 replace-in-prod，已随本切片从 .mcp.json 移除）；test-wan `:45` / prod-wan `:63` 裸 `${…_URL}`；5 条 `env` 均 `{}` |
| 6 | `project-with-adr` 落地需配 ADR（tier 名暗示） | **确认（政策语义）** | plan L539 D-013「memory×5 = project-with-adr（独立拍板后落地）」；代码只认 `project` → 须 flip 到 `project`；`-with-adr` 名 = 落地须 ADR/独立拍板。memory pg 独立库（plan L114「另一能力单独标识」）→ ADR 可论证投影安全（诚实前提：checkpoint 含 biz 派生行但读它无法绕 L1/L1b，5-lens 更正，详 ADR-037 / plan §13 C1） |
| 7 | Codex `env_vars` 白名单能否让子进程继承 HKCU env（vault §六 未评估，须 spike） | **precedent-proven（见 §Spike）** | `.codex/config.toml:19` `github env_vars = ["GITHUB_PERSONAL_ACCESS_TOKEN"]`（HKCU secret）+ #330 AC7 实机成功「走 env_vars 凭据链」；memory×5 用**同一** `env:{NAME:${NAME}}`→`env_vars=[NAME]` 机制 |

### 3.1 Spike 结果（Stage 0/8 前置去风险）

- **Spike 1/1b/1c（name→env→URL 解析）= PASS**（2026-07-17，scratch `.cmd`，未触真脚本）。
  Spike 1（`!%~1!`）+ 1b（`call set`）+ 1c（**endlocal-drop 定稿**）。关键发现：延迟展开下 `call set`
  对 `%NN`（percent-encode）安全但对裸 `!` 破坏（1b Case C `pa!ss`→`pa5433`）；**endlocal-drop**
  （discovery 后丢延迟展开 + 带出 NODE_PATH，再解析 URL）全过 A(control)/B(`%40` 保真)/C(裸 `!` 保真)/
  D(unset→exit 3)/E(缺 arg→exit 2）。显式失败语义 = tightening。设计见 [[[PLAN]_dual-agent-compat_pg-cred|PLAN]] §4.2。
- **Spike 2a（env_vars → HKCU 子进程继承）= precedent-proven**：github（#330 AC7 实机）与 memory×5
  机制逐字相同；`.codex/config.toml` header L5-8 明载「Codex sanitizes MCP child env and env_vars
  inherits the named variables from the parent environment」。
- **Spike 2b（全链路：Codex → pg-server-start.cmd 解析名 → 连库）= 待实施期实机核验**（需真投影后的
  config；D-015 trust 每工程师×每 worktree 人工；承 [[reference_codex_headless_windows_invocation|Codex
  headless 四坑]]）。由两个已证半环组成（Spike 1 + 2a），残余风险低 → 折为实施期 AC（Owner 协同）。

## 4 Risk Assessment

- **Level：High**。**无** §3.1 mj-agent 专属 4 项必停触发（不动 skills/system.md/qcm_catalog/SQL guardrail）。
- 升 High 之由：
  - **A14 硬停**：`.mcp.json` server inventory + credential mode 变更（`policies/ai-agent.md:94`
    `mcp-server-trust-posture-change`）。
  - **D-017**：manifest `mcp.servers` memory×5 档位翻转 = 真 trust-posture 变更（非 surface-match）；
    派生 `.codex/config.toml` + `.agents/**` 随之重生；**若** `agents_sync.py` 逻辑需改亦在 D-017 anchor 内。
  - **protected path**：`.claude/scripts/pg-server-start.cmd`（`.claude/**` harness 权限 prompt）。
  - **credential mode + 10-server 原子爆炸半径**：同一脚本服务 10 个 server，脚本契约改则 10 条
    `.mcp.json` args 必须原子改（否则 biz×5 传 `${...}` 给按名解析的脚本 → 静默错连）。biz×5 虽档位
    保持 `never`（不投影），其**运行时仍受同一脚本约束** → 波及但不投影。
- **缓解**：逐门独立拍板（不合并）；spike 前置；显式失败语义（env 未设 = 硬失败非静默）；negative test
  证零凭据投影（G7 + PJ044）；biz×5/ssh 永 `never` 不变（ADR-006/009）。

## 5 tightening（纪律收紧，须 Owner 明确接受）

A 会让 `.mcp.json` 3 条内嵌 default 消失（含 dev 的本地 throwaway 口令，自述 replace-in-prod）。
今日它们是「env 未设时仍能起 server」的兜底；改后 env 未设 = **显式失败**。这是**纪律收紧**（更安全：
消除第二处真相 + 消除字面凭据），但会改变新工程师首次 clone 的零配置 dev 体验 → 须：
① Owner 明确接受该体验变化；② 同步 `docs/guide/[GUIDE]_Developer_Onboarding.md`（若其记载零配置起 dev）。

## 6 Documentation Decision（粗评；Stage 3 Repo Scan 已在本 INTAKE §3 细化）

| Type | Action | 说明 |
| --- | --- | --- |
| INTAKE + PLAN | **Create** | 本对（family 惯例，state: active；merge 后独立 flip PR 翻 completed） |
| ADR | **Create（决策待定）** | memory×5 Codex 投影 ADR（`project-with-adr` 的 ADR 半边）——推荐路径；Owner 可改「拍板记录入 plan/issue，不单开 ADR」（§7 门 3） |
| GUIDE（Developer_Onboarding） | **Update（条件）** | 若移除零配置 default（§5 tightening） |
| adapters/development-agent.md | **None / 待核** | Stage 8 核对是否有 pg/memory 投影档陈述需同步 |
| SPEC / RUNBOOK / STANDARD / ISSUE / ASSESSMENT / CHANGELOG / INDEX | **None** | 无新模块接口；vault 评估已备料不入仓（承 S2 #330 AC10 先例） |

## 7 Owner 拍板记录 + 待拍门（2026-07-17）

**已拍**：
1. **切片锚 = B（pg-default）** / **议题 3 方案 = A（传名 + merge 议题 1）**（§2）。

**待拍（Stage 5 Plan HITL Gate + 逐门）**：
2. **A14**（`.mcp.json` 10-server 原子改）· **D-017**（manifest memory×5→project + 派生重生）·
   **protected path**（`pg-server-start.cmd`）· **commit/push/PR/merge** = 各自 `OWNER_APPROVAL_REQUIRED`。
3. **ADR 决策 = 单开 ADR**（Owner 2026-07-17 拍板）——memory×5 投影 ADR（下一可用号），论证
   memory≠biz、secrets by-name、biz×5+ssh 仍 never；作 W5 入 scope。
4. **tightening = 接受**（Owner 2026-07-17 拍板）——env 未设 = 显式失败（无 default，§4.2），同步 Developer_Onboarding。
5. **Spike 2b = 实施期实机核验**（Owner 协同）——非现在跑合成 Spike；Spike 1 + 2a precedent 覆盖两半环。
6. **待拍**（逐门）：**protected path**（W1）· **A14**（W2 `.mcp.json`）· **D-017**（W3 manifest + W4 派生重生）·
   **commit/push/PR/merge** = 各自 `OWNER_APPROVAL_REQUIRED`。

### 7.1 拍板前提溯源纪律（承 [[feedback_wrong_premise_voids_decision|#341/#344 教训]]）

写进 AskUserQuestion 选项的事实断言均 file:line 溯源（§3 表）。关键更正：#312 议题 3 两选项非对称
（断言 1）——「Codex 显式 env」单独不解投影，因 G-A 是无条件 `${` 子串测试（`agents_sync.py:273` +
`.mcp.json:45`/`:63` 裸引用实证）。原 #312 表述前提被证伪 → 带更正回 Owner，Owner 重拍 A；**动作面
未缩小反而收敛为单一可行路径 = correctness 更正**，原 #312 记录留档不覆盖。

## 8 Verification Plan

- **Level A（只读）**：`uv run python scripts/sdd/agents_sync.py --check --surface mcp`（V11）+
  `--surface skills`（V10）· `check_agents_projection.py`（V9）· `check_development_agent.py`（V8）·
  `uv run pytest tests/unit tests/eval` · `uv run ruff check` · `uv run mypy src/mj_agent`。
- **Level B（本机 / HITL）**：`agents_sync.py sync`（写派生产物）· 本机起 10 个 pg server 核验（Claude 侧）·
  实机 Codex `codex mcp list` + memory-server 查询（Spike 2b，Owner 协同）· negative test（env 未设 → 显式失败）。
- **不跑及原因**：smoke（无 LLM 行为改动）；biz 直连（数据边界，禁）。

## 9 交办事项（本切片范围外，登记以免丢失）

- **议题 2（ssh-manager wrapper）**——`settings.json:27` `mcp__ssh-manager__*` 单条通配收窄；各自为锚，需先出评估。
- **议题 1 的下游**——本切片即落地议题 1（memory×5→project）；无残留。
- **P4 本体 + S3 skills-gate blocking 转正**——日历腿 2026-07-28 才合格。
- **`policies/security.md:72` ADR-034 stale gloss**——已登记 [[[INTAKE]_dual-agent-compat_a6q3-cigates|#347 INTAKE]] §9，非本切片。

## 10 Next Step

Stage 4 Plan 已同批落盘（`[PLAN]_dual-agent-compat_pg-cred.md`）→ Stage 5 Plan HITL Gate（§7 待拍门）
→ Stage 8 实施（`/mj-agent-flow-implement`；逐门 W1→Wn 独立拍板）→ Stage 10 verify → Stage 11
self-review（大改用 5-lens 对抗审查）→ commit/push/PR 交 Owner → merge 后 flip PR 翻 state completed。
