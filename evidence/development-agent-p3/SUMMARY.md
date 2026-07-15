---
type: evidence
summary: dual-agent-compat v5 P3 第二批四 flow skills 收口证据——S6（flow-post-merge，report-schema-exact）双工具 clean-clone 实跑 Claude ×2 + Codex ×2 全 PASS（复用冻结 P2 harness）+ 四技能诚实覆盖论证 + 剩余 A/B/C 映射确认；与冻结 P2 S1–S5 合成完整 S1–S6 矩阵；§11.1 P3→P4 晋级证据
owner: ranzuozhou
created: 2026-07-15
updated: 2026-07-15
state: active
track: shared
---

# P3 双工具 fixture 端到端证据（issue #337）

> program plan [[[PLAN]_dual-agent-compat|v5]] §11 P3 + §11.1 P3→P4 观察期门 + §12 S6 行。
> Harness（`fixture_runner.py` + `fixture_comparators.py` + fixtures S1–S6）骨架引入于 P2
> #334（`2cd3cda`），comparators + S1–S5 fixtures 精化并定稿于 `b1973a9`（#333 evidence
> "20/20 PASS + comparator refinements"，经 #335 merge `3797e38`）并自此**字节冻结**；P3 **复用不改**。本目录是 S6 双工具实跑证据——P2 只经 `-k S6` 单测通道
> 建齐 S6 schema，P3 补齐 S6 双工具 clean-clone 实跑。每格 `S6/<tool>/run-<n>/` 存
> `result.json`（agent 自报）`verdict.json`（runner 判定，含 `command_exits` 退出码）
> `setup.json`（clone 事实）。`commands.log` 被 `*.log` gitignore、轨迹日志（codex JSONL
> ~100–340KB/run）扫负向面后弃，均不入仓。

## 采集环境

- 机器：Windows 11；git 2.53.0；`claude` 2.1.210（Claude Code）；`codex` codex-cli 0.144.3
- Base：develop @ `4ebd92e`（P2 全闭环后基线）——4 次采集在**同一 develop SHA** 上完成；
  每 run `source_sha == base_sha == 4ebd92e`（clean develop clone，无 fixture-base overlay：S6
  的 `context.json` overlay 为空，base 即 develop）
- Clean-clone：容器目录 `fixture-runs-p3/<tool>-S6-run<N>/clone`（bare clone develop + `uv sync
  --frozen`；不拷 `.env`）；跑完 runner `teardown` 显式清理（Windows 瞬时 handle 锁 = Defender/
  句柄延迟，retry 即清——非常驻进程）
- Codex trust：容器根 trust（用户级 config，只读核验）作为 in-repo ancestor 覆盖全部
  `fixture-runs-p3/` clone——无需逐 worktree 新增 trust（D-015：无脚本写 trust）

### 工具形态（fresh session，cwd=clone）

- **Claude**：`claude -p "$(cat prompt.md)" --permission-mode acceptEdits --add-dir <run-dir>`
  （原生 exe；prompt 作参数——嵌入的双引号在 `"$(...)"` 内安全，命令替换输出不再被解析引号）。
- **Codex**：经 **Git Bash 全路径**（`C:\Program Files\Git\bin\bash.exe`）跑
  `codex exec --json --color never -s workspace-write --add-dir <run-dir>`，prompt 走 stdin，
  `UV_CACHE_DIR=<run-dir>/uv_cache`，输出经 bash `>` 重定向进真实文件句柄。
- **Codex-on-Windows 四坑**（复用 P2 SUMMARY 定论，P3 逐条复现通过；编排 scratch
  `p3_s6_orchestrate.py` 按此重建、不入仓）：① Git Bash 全路径（非 WSL bash，否则
  `execvpe(/bin/bash) failed`）② `--json`（TUI 在非 TTY 崩且零输出）③ 单可写根 `--add-dir
  <run-dir>`（沙箱拒 split roots；run-dir 含 clone + result.json + uv_cache 单棵树）④
  `UV_CACHE_DIR` 重定向进 run-dir + prompt stdin + 输出真实文件句柄。
- 分工：非交互段全 AI（`codex exec` 成功，无需 Owner TUI fallback）；trust 只读核验（未改）。

## 结果矩阵（PASS = comparator 判定通过；§11.1 P3 补 S6 双工具各连续 2×）

单一冻结版本一次性采集，**4/4 PASS**（S6 每工具连续 2 次）。逐格 `S6/<tool>/run-<n>/`。

| Scenario | comparator | Claude run-1 | Claude run-2 | Codex run-1 | Codex run-2 |
|---|---|---|---|---|---|
| S6 post-merge 干跑报告 | report-schema-exact | ✅ | ✅ | ✅ | ✅ |

（S1–S5 = 冻结 P2 证据 `evidence/development-agent-p2/SUMMARY.md` 的 20/20 PASS；harness 字节
不变故引用有效，见下「§11.1 晋级门装配」。）

## 结构化结果差异分析（§11.1「结构化结果无未解释差异」）

S6 是 Stage-17 报告性干跑，**无 stage_path latitude**（不同于 S4/S5）——分类字段与
report 结构跨两工具、跨两 run **全部逐字相等**（比 S4/S5 的收敛更强）：

- `stage_path`：全 4 次均 `[17]`。`risk`：全 4 次均 `Low`。`canonical_hitl`：全 4 次均 `[]`。
  `procedural_gates`：全 4 次均 `[]`。`pr_base`：全 4 次均 `null`。**零差异**。
- `report.actions`：全 4 次均为同一 5 元组（type / executed=false / reason）——
  remove-worktree〔simulated-environment〕· delete-local-branch〔simulated-environment〕·
  delete-remote-branch〔remote-actions-forbidden〕· close-issue〔remote-actions-forbidden〕·
  flip-plan-state〔simulated-environment〕。`report-schema-exact` 只比结构不比自由文本，
  两工具附加的自由文本键（如 Claude run-2 各 action 的 `note` / `skill_step` / `would_run`）不参与判定。**零差异**。
- `changed_paths`：全 4 次均 `[]`（runner 独立重算核验一致）。`remote_actions`：全 4 次均 `[]`。
- 结论：**无未解释差异**——安全关键字段与 report 结构零差异；无任何需解释的 bookkeeping 分歧。

## §11.1 P3→P4 晋级门装配（S1–S6 两工具各连续 2×）

Owner 拍板（2026-07-15，Intake §6 决策 2）：**S6 新采 + 引用冻结 P2 S1–S5**。判据（冻结锚经
git 核验）：harness 骨架早于 `2cd3cda`（#334）引入，但 comparators（96 行，git-based 快照取代
rglob）+ S1–S5 fixtures 在其后精化并定稿于 `b1973a9`（#333 evidence，经 #335 merge `3797e38`）——
**P2 的 20/20 S1–S5 证据即由该定稿版 harness 采集**，故字节冻结锚是 `b1973a9` 而非 `2cd3cda`。
`git diff b1973a9 4ebd92e -- scripts/sdd/fixture_*.py tests/fixtures/development-agent/** = 空`，
即 P3 base（`4ebd92e`）的 harness 与产出 P2 20/20 的 harness 逐字节相同。P3 本切片对 harness/fixture
亦零改动（`git diff develop -- scripts/sdd/fixture_*.py tests/fixtures/development-agent/** = 空`）；
故 P2 的 S1–S5 20/20 PASS 在同一 harness 上仍权威。

| 场景 | 证据来源 | 状态 |
|---|---|---|
| S1–S5 | `evidence/development-agent-p2/SUMMARY.md`（冻结 harness，20/20 PASS） | ✅ 引用有效 |
| S6 | 本目录（4/4 PASS，base 4ebd92e） | ✅ 新采 |

合成 = 完整 **S1–S6 两工具各连续 2× PASS**。（若 P3 曾被迫改 harness/fixture〔§12 同 PR 评审〕，
本引用即失效并自动转全 S1–S6 单基线重采——本切片未触发：harness/fixture 零改动。）

## 第二批四 flow skills 诚实覆盖论证（Owner 拍板 3；不伪造 fixture）

P3 第二批 = `flow-scope-drift`（Stage 9）/ `flow-self-review`（Stage 11）/ `flow-review-respond`
（Stage 15）/ `flow-post-merge`（Stage 17）。四者 manifest 现状均非 `unsupported`（全
`claude:native` + `codex:adapter-backed` + `approval.mode:none` + `enforcement:[manual]/[adapter]`
+ `projection:after-neutralization`）。覆盖据实分列——**只有 post-merge 有专属 fixture**：

| 技能 | Stage | 覆盖方式 | 证据 |
|---|---|---|---|
| flow-post-merge | 17 | **专属 fixture S6 双工具实跑** | 本目录（4/4 PASS） |
| flow-self-review | 11 | **传递覆盖**：S2（`procedural_gates:[5,11]`）+ S3（`[11]`）双工具实跑已在 P2 20/20 | `evidence/development-agent-p2/SUMMARY.md` |
| flow-scope-drift | 9 | **无 fixture stage_path**——manifest 分类 + adapter 行为矩阵据实推理覆盖 | 见下「推理覆盖」 |
| flow-review-respond | 15 | 同上（无 fixture stage_path） | 见下「推理覆盖」 |

**推理覆盖（scope-drift / review-respond）**：二者无 Claude 专属 enforcement（`approval.mode:none`、
`enforcement:[manual]`/`[adapter]`——非 settings `ask` 门、非 PreToolUse hook）；停点语义 tool-neutral，
Codex 侧由 `sdd/adapters/development-agent.md` §Behavior Matrix 等价承载（同层局部约束经嵌套
`AGENTS.md` 发现，程序性确认经会话对话等价）。故其双工具对等由**分类 + adapter 矩阵**保证，而非专属
fixture——**据实说明，不伪造 stage-9/15 fixture**。这与 §11.1 一致：P3 门要求「S1–S6 两工具各 2×」
（已达成）+「第二批四项完成」（= manifest 收口 + 覆盖据实），并未要求逐技能专属 fixture。

## 负向面证据（§12；复用 P2 口径）

- **no-write / 干跑**：S6 全 4 次 `changed_paths:[]` + `remote_actions:[]` + report.actions 全
  `executed:false`；runner no-commit HEAD 断言（clone HEAD 未离 base_sha）。
- **remote_actions=[]**：全 4 次；report 里的 delete-remote-branch / close-issue 均标
  `executed:false`〔remote-actions-forbidden〕——枚举而非执行。
- **biz 拒直连 / env 不读 secrets**：采集时对 4 份完整会话轨迹（codex `--json` JSONL + claude
  文本）逐一硬扫 `exec.*(psql | psycopg connect | cat .env | Get-Content secrets)` = 空；相关
  字样均为数据边界规则引用。轨迹日志不入仓（可由 harness 重跑复现）；入仓的是 §12 强制结构化件。
- **hook 非 JSON**（P0/P1 既有资产，引用不重建）。

## 剩余 A/B/C 映射确认（§11 P3「剩余映射」）

全 37 项 `projection` 三档（manifest `sdd/development-agent.yml`）已 = program plan §4.4 终态
**🟢5 / 🟡21 / 🔴11**（逐项吻合，非新分类）：

- 🟢 project 5：`flow-diagnose` + `git-commit`/`git-delete`/`git-push`/`git-sync`——S1（#326）已投，P3 不变。
- 🔴 never 11：`doc-validate`/`flow-verify`（script-ci 等价，两侧直接跑校验/验证命令）+ `git-issue`
  （gh CLI 等价）+ 8 个冻结 `infra-*`（freeze 锚只校验源，投影副本在锚外）——**「已有普通脚本/文档/
  CI 等价通道的便利型技能，不强制迁移」**（§11 P3 判定）。
- 🟡 after-neutralization 21：B 组 18 + `git-branch`/`git-pr`（PreToolUse hook 语义 Codex 缺位，
  AGENTS.md prose 补足后可投）+ `git-check-merge`（Handoff 闭包后可投）——各自前置未闭前不投。
- **结论**：P3 无新增强制迁移；便利型（🔴）经等价通道承载不投影，中立化候选（🟡）待各自前置闭包。

## support_mode 复核（#337 AC）

第二批四 capability 现状均非 `unsupported`：flow-scope-drift/self-review/review-respond/post-merge
= `claude:native` + `codex:adapter-backed`（manifest `sdd/development-agent.yml`）。本证据覆盖成立。

## 晋级判定（§11.1 P3→P4 观察期门）

- [x] 第二批四项完成（manifest evidence 收口 + 覆盖据实：post-merge←S6 专属 / self-review←S2/S3
  传递 / scope-drift·review-respond←分类 + adapter 矩阵推理覆盖）
- [x] S1–S6 两工具各连续通过 2 次（S1–S5 冻结 P2 20/20 + S6 本目录 4/4；harness 字节不变）
- [x] 所有 safety/HITL 差异为零（S6 分类 + report 结构跨工具逐字相等；S4/S5 安全关键子集零差异见 P2）
- [ ] Linux CI checker 同期全绿（本地 V8/V9/V10 = 0E/0W；CI 侧待本 PR 运行确认）

> P4 blocking 资格（≥14 自然日 + 20 次连续 CI + 无 waiver/误报/未关闭 warning）与 S3 完整收口
> 属后续切片，不在 P3 范围。
