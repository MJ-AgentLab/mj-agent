---
type: plan
summary: 双工具兼容 v5 S2 执行计划（issue #330）——MCP 面：3 spikes 全 PASS（进拍板）后 emitter B（github/playwright/serena+codex-context 三 project 档 + env_vars 按名 + posture 转写）+ 路径形 lock 保留键 + V9 PJ04x + MCP gate day-1 blocking（V11 独立 step + real-tree pin）+ G7 内容扫描扩展；2-PR（实施一体 + flip）
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-14
state: active
track: shared
---

# [PLAN] 双工具兼容 v5 — S2 执行计划（issue #330）

## 1. Linked Artifacts

- Issue: #330（S2 执行）· 总锚 #312 · Program plan: [[[PLAN]_dual-agent-compat|v5 计划]]（§8 生成器条款 / §10 投影 checker 规则 / §11 S2 / §11.1 / §12 投影域验收 / §17 gates）
- Intake: [[[INTAKE]_dual-agent-compat_s2|Stage 0 Intake]]（2026-07-14；4 项拍板：锚定 S2 / spike 方案 / 2-PR / settings biz allow 收窄同期评估）
- Spike 证据：vault `claude-codex-agent-kernel/mj-agent/[EVIDENCE]_s2-spike-capture-2026-07-14.md` + #330 comment（AC1 记录；3 spikes 全 PASS + 进拍板 + 3 项随行设计拍板）
- Repo Scan: Stage 3 对话输出（2026-07-14；develop @ `c866029` 基准）
- 既定机器契约（S1 遗产，不得另立口径）：`agents_sync.py` 显式分支模式（README/lock 同款）、lock 扁平 `{key: "sha256:<body_sha256>"}` 排序单行、LF 归一比较、`main(argv, repo_root)` 注入、ASCII 输出、exit 0/1/2；V9 `run_checks` 聚合 + `WATCHED_PREFIXES` 已含 `.codex/`

## 2. Context

S1（#326）闭环：emitter A + 5 技能投影 + V10 drift gate warning 已入仓；§11.1 S1→S2 晋级证据三项齐。S2 硬前置 3 spikes 于 2026-07-14 全 PASS（判定与陷阱登记见 vault 证据包），Owner 进拍板 = emitter B 全套。

Spike 直接设计输入（已拍板/已核验）：

1. **env 机制**：codex 默认清洗 MCP 子进程 env（HKCU 秘密不透传）；`mcp_servers.<id>.env_vars = ['NAME',...]` 按名白名单继承实证生效 → emitter 把源侧 `env` 的 `${VAR}` 改写为 `env_vars` 名单，**TOML 永无字面秘密**。
2. **trust 语义**：project 层仅 trusted 加载；trust 匹配 = 精确条目或**仓内祖先条目**（Owner 容器条目 `d:\...\mj-agent` 实测覆盖全部 worktree）→ 合入后 develop/新 worktree 的 Codex 自动加载产物，**无需逐 worktree trust**；安全对偶 = 任意分支产物自动加载，正当化 day-1 blocking + G7 + A14 邻接。
3. **serena transform**：`--context claude-code` → `--context codex`（上游 `codex.yml` 已核验）；`--project-from-cwd` 保留（MCP 子进程 cwd = worktree 根实证）。
4. **官方黑名单**：project 层忽略键不含 `mcp_servers`（config-reference 核验）——②的 medium→high 风险解除。

风味判定：全切片 C（生成器/checker/CI/tests/治理文档 + 新生成产物）。§3.1 必停 4 项不触发；A14 不触发（`.mcp.json` 只读）；High 来自 `ci-blocking-gate-toggle`（拍板已记 #330 comment）+ `.codex/config.toml` 受保护邻接面创建（§17）。

Stage 3 关键设计裁定（随行拍板 ×3，记录于 #330 comment）：

1. **lock = 路径形保留键**：`.agents.lock.json` 增 `".codex/config.toml": "sha256:<body_sha256(LF)>"`（TOML 无 frontmatter → 全文哈希）；V9 `check_lock` 放行该保留键（免 PJ034），新 PJ04x 校验其一致性——两侧同 PR 协调改。
2. **gate 载体 = V11 独立 blocking step + real-tree pin 双保险**：新 CI step `agents_sync.py --check --surface mcp`（**无** `continue-on-error`）；V10 step 改 `--check --surface skills`（保 warning，skills 面转正仍属 S3/P4）；`tests/unit` 新增 `test_real_tree_mcp_projection_in_sync` 走 blocking Tests step（V8/V9/V10 真值注记同族）。**此即 D-016 day-1 blocking 的 `ci-blocking-gate-toggle` 显式执行记录落地**。
3. **`--surface {skills,mcp,all}`**：`--check` 新增可选参数，默认 `all`（本地一把梭不变）；`sync` 恒双面（单动作作者侧）；`--adopt` 天然拒 mcp 面（whitelist 校验不识路径键，TOML 无源可反灌）。

## 3. Scope

- 包含：emitter B（`.codex/config.toml` 生成 + reconcile + lock 保留键）· V9 `check_codex_config`（PJ04x）+ `check_lock` 保留键放行 + `load_mcp_projection` loader · V11 blocking step + V10 step 收窄 skills 面 · G7 第 4 检查（内容扫描）· 单测（golden/幂等/transform/负向/real-tree pin）· AGENTS.md/adapter/gates.md/.claudeignore 文档面 · plans 2 件 · settings biz allow 收窄评估（**仅评估产物**，AC10）
- 不包含：`pg-mj-agent-memory-*`×5 投影（project-with-adr 独立拍板）· `.mcp.json` 任何改动（A14；emitter 只读）· manifest `mcp`/`codex.posture` 段修改（D-017；只读）· biz×5/ssh-manager（永 never；PJ044 反向钉死）· skills gate V10 blocking 转正（S3/P4）· doctor（S3）· Path B · 用户级 `~/.codex/config.toml` 任何代写（D-015）
- 前置依赖：S1 已 merge（develop @ c866029）；3 spikes 全 PASS + 进拍板（已完成）

## 4. 任务拆解（Stage 8 编号 · 全部风味 C · 单实施 PR `maintain/330-s2-mcp-projection`）

- **8a emitter B（`scripts/sdd/agents_sync.py`）**：
  - 新常量 `CODEX_CONFIG_RELPATH = Path(".codex/config.toml")`；新 loader（放 `check_agents_projection.py` 与 V9 共用）`load_mcp_projection(repo_root)` → 读 manifest `mcp` 段（project 档 server 名集 + serena transform 记号 + never 档名集）+ `codex.posture` 键值；读 `.mcp.json` 取 server 定义。
  - TOML 生成 = 手写模板纯字符串拼装（写不引 toml 库；读校验用 stdlib `tomllib`）：GENERATED 头注（所有权 + 修改路径 + D-011/D-012 指针）→ posture 三键（manifest 顺序：`approval_policy`/`sandbox_mode`/`project_doc_max_bytes`）→ `[mcp_servers.<name>]` 按名排序：`command` + `args`（serena 档应用 `--context` transform）+ `env_vars`（由源 `env` 的 `${VAR}` 提取名字排序；源 `env` 出现**非** `${VAR}` 字面值 → `FatalCheckError` exit 2，fail-closed）；`type: stdio` 不转写（codex stdio 隐含）。LF 写盘（`.gitattributes` 已 pin `*.toml eol=lf`）。
  - `sync`：显式分支模式（同 README/lock）——重算文本、LF 归一比较、差异才写；`.codex/` 树 reconcile：`config.toml` 之外任何文件/目录删除（--check 则 flag）；lock 并入保留键重算。
  - `--check --surface {skills,mcp,all}`（默认 all）：mcp 面 = regenerate-and-diff（产物 ≟ 重算文本，LF 归一）+ `.codex/` 多余文件 + lock 保留键一致；drift → exit 1 + 规定动作文案（「改源 `.mcp.json`〔A14 必停〕或 manifest `mcp`/`codex.posture`〔D-017 拍板〕→ `agents_sync.py sync` → 同 PR 提交；产物不可手改；merge 冲突 = merge 源重跑 sync」）。
  - 验证：`--check` exit 0；`sync` 幂等二跑零 diff；手改产物/改 `.mcp.json` 未 sync → 1 + 文案。
- **8b V9 扩展（`scripts/sdd/check_agents_projection.py`）**：`check_codex_config` 挂 `run_checks` 第 4 位——**PJ040** config 存在性与 mcp-project 集配对（空集有文件 / 非空集缺文件）；**PJ041** config 内 server 集 ≟ manifest project 集（含多出 server）；**PJ042** lock 保留键存在性配对；**PJ043** 保留键哈希 ≟ 实盘 config `body_sha256(LF)`；**PJ044** never 档 server 名（`pg-mj-system-biz-*`/`ssh-manager`，从 manifest 读）出现在 config → error（数据边界泄漏钉死）。`check_lock` 放行路径形保留键。`--changed-from` 零接线（`.codex/` 已在 `WATCHED_PREFIXES`）。
- **8c G7 扩展（`scripts/sdd/check_secret_exposure.py`）**：第 4 检查 `_check_codex_config`（tomllib 解析；文件缺失 = 空缺性 PASS，fork/无 secrets 不假红）——任何 `[mcp_servers.*.env]` 表存在 = FAIL（emitter 永不产 env 表，出现即手改/字面注入）；args/顶层字符串含 URL userinfo 密码形态（`://user:pass@`）或 `password=`/`token=` 字面赋值 = FAIL；`env_vars` 名单 = 合法（按名引用）。基线 3P→4P。**blocking 主防线 = V11 drift**（任何偏离生成文本即红）；G7 内容扫描为纵深防御（G7 gate 保持 warning@ci 姿态不变，非本切片 flip 对象）。
- **8d 单测（`tests/unit/test_agents_sync.py` + `test_sdd_development_agent.py`）**：复用 `make_repo(mcp_servers=...)` 预埋——emitter golden（合成 manifest+.mcp.json → 精确 TOML 文本）；幂等；serena transform；`${VAR}`→`env_vars` 提取排序；字面 env → exit 2；`.codex/` 多余文件 reconcile（sync 清 / check flag）；lock 保留键（存在性 + 哈希 + V9 互认集成）；`--surface` 三值行为 + 与 `sync` 互斥沿用；跨 EOL 稳定（toml 已 pin 仍 LF 归一钉线）；PJ040-PJ044 各一负向用例（含 never 档泄漏）；**real-tree pin**：`test_real_tree_mcp_projection_in_sync`（`--check --surface mcp` exit 0）+ 既有 pin 回归。
- **8e 产物入仓**：实跑 `agents_sync.py sync` → `.codex/config.toml`〔新〕+ `.agents.lock.json`（增保留键）同 commit（PJ042 配对纪律，同 S1 8f/PJ030 先例）。
- **8f CI（`.github/workflows/ci.yml`）**：V10 step 命令改 `--check --surface skills`（名称/注释同步；warning 姿态不变）；其后新增 **V11 step**（block 内、end-marker 前）：name 注明 BLOCKING day-1 per D-016 + Owner 执行记录 #330，`run: uv run python scripts/sdd/agents_sync.py --check --surface mcp`，**无** `continue-on-error`；块注释补 V11 描述。
- **8g 文档面**：根 `AGENTS.md`「Generated projections」段扩 `.codex/config.toml`（生成物三件套→四件套；修改路径含 A14/D-017 分流；Codex 消费语义 = trusted 项目自动加载 + 容器 trust 覆盖 worktree 事实 + Desktop 重写陷阱一句话）+ footer 注记；`sdd/adapters/development-agent.md` :36 移入 Scope Included / :100 V9 cell 补执行记录 / :114 状态 flip + V11 行；`sdd/gates.md` §2 V10 行补 surface 注记 + 新 **V11 Codex-MCP-Projection** 行（blocking@ci day-1，D-016 + #330 执行记录）；`.claudeignore` 加 `.codex/`；`.agents/README.md` 模板句子扩（提及 config.toml 同属生成物家族）→ 随 sync 重生成。
- **8h settings biz allow 收窄评估（AC10，非实施）**：借 spike 摸清的用户级布线（postgres-*×5 env 表字面值 + ssh-manager 全局在线）评估 `.claude/settings.json` biz allow 收窄面；产物落 vault，结论清单待独立拍板；不进本 PR 代码面。
- **8i 收口**：全量 Level A + drift 演练 + GitHub CI 实跑（V11 出现且 blocking 绿；ubuntu golden 稳定）+ Codex 实机连通（AC7，Owner TUI 配合）+ #330 AC 勾选 + adversarial review（canonical 产物 single-agent 编写 + 大闭幕对抗审查，per 既有偏好）。

### Documentation Decision（§7.1 摘要）

Plan=Create（本 2 件，PR-1 携带）；SPEC/ADR/RUNBOOK/GUIDE/STANDARD/Local ISSUE/ASSESSMENT/CHANGELOG/INDEX=None（ADR-036 D-011~D-017 已收口；收窄评估落 vault 非 canonical；CHANGELOG 按 S1 先例 None）。

## 5. 风险（Risk Level: High）

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| V11 day-1 blocking 偏离块内 warning-first 惯例引质疑 | Low | C | D-016 预拍 + #330 comment 显式执行记录 + step name/gates.md 双登记；rollback = revert step（另走 toggle HITL） |
| 容器 trust 使恶意分支产物自动加载（spike ③ 安全对偶） | Medium | C | V11 blocking（任何偏离即红）+ PJ044 never 档泄漏钉死 + G7 纵深 + `.codex/config.toml` A14 邻接必停 + PR 人审 |
| lock 保留键破坏 V9 既有互认 | Medium | C | 两侧同 PR 协调改 + V9 集成单测（sync 产物喂 `v9_main`）+ real-tree pin 双钉 |
| emitter 与 `.mcp.json` 源漂移（源人工维护） | Medium | C | V11 regenerate-and-diff 恒比对源→红 + `WATCHED_PREFIXES` 已含 `.codex/`；规定动作文案给 A14/D-017 分流 |
| 源 `env` 混入字面值被静默投影 | Low | C | fail-closed：非 `${VAR}` 形态 → exit 2 拒生成 + 单测钉住 |
| G7 内容扫描误报（TOML 合法结构被判凭据） | Low | C | 规则窄化（env 表存在性 + userinfo/字面赋值形态）+ 单测正反用例；G7 保持 warning 姿态 |
| `--surface` 改 V10 调用形态碰旧脚本兼容 | Low | C | `--check` 默认 all 向后兼容；仅 CI 调用点显式收窄；单测钉三值 |
| CI/workflow 编辑被 classifier 拦 | Low | C | 交互模式权限 prompt = 拍板载体；被拦一次即停交 Owner（既往教训） |
| fork/无 secrets 假红 | Low | C | 生成/校验零 env 解析（名单是名字非值）+ 文件缺失空缺性 PASS + CI 本身即无 HKCU 环境实证 |

## 6. 验证

### 6.1 Stage 10 Level A（只读 / 必跑）

```
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit tests/eval -q          # 本 worktree 无 .env，#298 假红不适用
python -m compileall src
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
uv run python scripts/sdd/check_development_agent.py --all --fail-on error
uv run python scripts/sdd/check_agents_projection.py --all      # 含 PJ04x 后仍 0E/0W
uv run python scripts/sdd/agents_sync.py --check                # all 面 exit 0
uv run python scripts/sdd/check_secret_exposure.py --all        # 4P/0W/0F
uv run python scripts/sdd/check_claude_skill_contracts.py --all # 37/37 回归
```

- 附加演练：手改 `.codex/config.toml` → `--check --surface mcp` exit 1 + 规定动作；临时改 `.mcp.json` 副本喂合成仓测源漂移（真 `.mcp.json` 不动）；`sync` 幂等二跑 `git status --short` 空。

### 6.2 Level B

- GitHub CI 实跑：V11 step 出现且 blocking 绿、V10（skills 面）warning 绿、Tests step 含 real-tree pin 绿 = ubuntu golden 证据 + fork-like 无 secrets 实证。
- Codex 实机（AC7；Owner TUI 配合）：trusted worktree 内 `codex mcp list` 见 github/playwright/serena 三档；实调各一（github 走 `env_vars` 凭据链、serena `codex` context 启动、playwright 启动）——exec 非交互 approval 限制在案，实调走交互 TUI。

### 6.3 Stage 11 tie-in

- 反向扫描：不改函数/路径/表名/biz 面——5 类反扫不触发；'emitter A'/'S2 未落地' 陈述由 8g 消化（repo-scan 触点清单闭合）。
- scope-drift 预期：Severity ≤ Minor（新增 = 1 产物 + lock 增 1 键 + PJ04x + V11 step + G7 第 4 检查 + 单测 + 文档 5 处 + plans 2 件）。

## 7. 完成标准（AC，对齐 #330）

- [ ] AC1 ✅（3 spikes + 进拍板，2026-07-14 已记 #330 comment）
- [ ] AC2 `sync` 幂等产出三档 TOML（transform + env_vars 按名，零字面秘密）
- [ ] AC3 golden 双平台字节稳定 + real-tree pin
- [ ] AC4 产物手改 → checker 红 + 规定动作文案
- [ ] AC5 V11 blocking step 挂 CI 无 continue-on-error；fork/无 secrets 不假红；toggle 执行记录在案
- [ ] AC6 G7 覆盖 config.toml 字面凭据形态（4P 基线）
- [ ] AC7 三档 Codex 实机连通 + 叠加语义复核结论落档（spike 证据包已含，实调补齐）
- [ ] AC8 Level A 全绿
- [ ] AC9 AGENTS.md/gates.md/adapter/.claudeignore 文档面落地
- [ ] AC10 settings biz allow 收窄评估产物（待独立拍板）
- [ ] 2 PR 依序 merge（PR-1 → 核对 PR-2 base → 合；均 `--delete-branch`，合并交 Owner）；#330 关闭；#312 S2 行勾选

## 8. 关联

- Issue: #330 / #312（总锚）
- 目标文件：`scripts/sdd/agents_sync.py` · `scripts/sdd/check_agents_projection.py` · `scripts/sdd/check_secret_exposure.py` · `.codex/config.toml`〔新·生成〕· `.agents.lock.json` · `.agents/README.md`（模板扩随 sync 重生成）· `tests/unit/test_agents_sync.py` · `tests/unit/test_sdd_development_agent.py` · `.github/workflows/ci.yml` · `AGENTS.md` · `sdd/gates.md` · `sdd/adapters/development-agent.md` · `.claudeignore` · plans 2 件〔新〕
- 不动文件：`src/mj_agent/**` · `.mcp.json`（A14；只读）· `sdd/development-agent.yml`（D-017；只读）· `.claude/settings.json`（收窄仅评估）· `.claude/skills/**`（本切片零技能源编辑）· `config/secrets*` / `.env` · `.gitattributes` · 用户级 `~/.codex/**`（D-015）
- 后续独立 PR / 议题：PR-2 state flip；S3（doctor + skills gate 转正 + 2 独立议题）；#312 递延议题（memory×5 project-with-adr / ssh wrapper / pg 凭据 default 单一真相）；收窄评估拍板后的实施切片（若采）
