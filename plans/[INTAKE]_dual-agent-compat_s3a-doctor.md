---
type: intake
summary: 双工具兼容 v5 第十一执行切片（#312 S3 收口的 doctor 只读子切片 = S3a）的 Stage 0 Intake 落盘——scripts/sdd/agents_sync.py 新增只读 doctor 模式（trust 只读报告 + setup-mcp-secrets.ps1 -Reload HKCU 核对 + 双发现 canary 报告）；maintain/Medium/1 PR；对应 issue #350（总锚 #312）；3 项 Owner 拍板（锚 = C〔S3a doctor 只读版〕 / 范围 = doctor 只读 only〔skills gate blocking flip 留 P4、3 独立议题各自为锚〕 / canary = 保留 unit test + doctor 增补只读报告〔非「迁入」删测〕）+ Stage 0 核查对 brief 的确认与更正（§3）
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — S3a doctor 只读切片（issue #350）

> Stage 0 输出于 2026-07-16 会话内产生并当日落盘（worktree `maintain/350-s3a-doctor` 内，保
> develop 干净）；触发 §2.1 落盘判定（HITL 点 ≥ 3〔锚拍板 + 范围拍板 + canary 拍板 +
> commit/push/PR〕 + 家族 `[INTAKE]_+[PLAN]_` 成对惯例 + 多子检查切片）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §S3（L256/L315，doctor 完整版三件套）+
> [[decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] D-015（doctor 只读红线）
> + 总锚 #312（S3 复选框）。

## 1 Task Classification

- **Type**：`maintain`（`scripts/sdd/` 工具面；分支前缀 `maintain/`，承 S1 `maintain/326-s1-agents-sync`
  / S2 `maintain/330-s2-mcp-projection` 先例；commit 类型 `feat(sdd)`——新增 agents_sync 模式）。
- **Base branch**：`develop` → PR base `develop`。
- **估计影响范围**：`scripts/sdd/agents_sync.py`（新增 `do_doctor` + `doctor` 子命令 + 模式互斥 +
  docstring/help 去「doctor lands at S3」）· `tests/unit/test_sdd_development_agent.py`（doctor 测试）·
  `sdd/adapters/development-agent.md`（:94 / :129 两行状态更新）· `plans/[INTAKE]+[PLAN]_…_s3a-doctor.md`。
  **只读、不写**：`~/.codex/config.toml`（trust）· `.mcp.json` · `sdd/development-agent.yml`（manifest）·
  `.claude/skills/*`；子进程调既有 `.claude/scripts/setup-mcp-secrets.ps1 -Reload`。**不进 CI**。

## 2 锚选定（Step 1）

Owner 2026-07-16 AskUserQuestion 拍 **C（S3a doctor 只读版）**——从候选 B（pg-default）/ C /
E（ssh-manager wrapper）/ A（A6 durability gate）中选；**D（P4 本体）结构性出局**（日历腿
2026-07-28 才绑定，§11.1 AND，见 [[[PLAN]_dual-agent-compat_a6q3-cigates|上切片]] 与总锚）。
理由：C 近乎可实施（唯一真开放点 = canary 处置，已由 Owner 二次拍板解开），推进 S3 轨道，P4 等待窗口内
最 ready 的前向进度，且 `scripts/` 工具面完全在 P4 gate 机制之外。

## 3 Stage 0 核查产出——对 brief 的确认与更正

| # | brief 断言 | 核查结果 | 证据 |
| --- | --- | --- | --- |
| 1 | `DA059 不存在系历轮 brief 幻觉` | **确认为真** | `grep -rn "DA059" scripts/ tests/` 零命中；实存 DA 码 = DA002/005/013/015/021/023/032/042/053/060/061/073 |
| 2 | `test_real_tree_v8_all_passes:135-136 是第二道 blocking canary 执行者` | **确认为真** | 该测跑 `v8_main(["--all"])` → 含 DA060（on-disk skill 缺 manifest = error） |
| 3 | `CLI 形态/退出码/-Reload 三项经读代码可定（非 Owner 问题）` | **确认为真**——已由本切片自定：CLI = 位置子命令 `doctor`（承 plan L193）；退出码 = 0（报告成，含 warning）/2（fatal）；-Reload 既有产出（掩码 + 缺失清单）直接复用 | agents_sync.py:543-631 / setup-mcp-secrets.ps1:120-150 |
| 4 | `唯一真 blocking 未决 = canary 处置` | **确认为真且确为 Owner 面**——不是措辞而是「是否弱化 CI 强制」的真分叉（见 §7 拍板 3） | plan `_p1s0.md:23/45`「S0 canary 以 unit test 承载（S3 迁入 doctor）」vs doctor 不在 CI |

> 关键澄清：plan L193 把 doctor 列为**子命令**（`sync` / `--check` / `doctor` / `--adopt`）→ 本切片
> 采位置参数 `choices=["sync","doctor"]`（非 `--doctor` 旗标），与 `sync` 同形。

## 4 Risk Assessment

- **Level：Medium**。**无** §3.1 mj-agent 专属 4 项必停触发（不动 skills/system.md/qcm_catalog/SQL guardrail）。
- 升 Medium（非 Low）之由 = **安全邻接**：① **D-015 只读红线**——doctor 若写 `~/.codex/config.toml`
  trust 即成供应链洞；② 读 env/secret 邻接面（HKCU 变量、`~/.codex/config.toml`）。
- **缓解**：只读构造 + 一条「doctor 写零文件」断言测试；`-Reload` 已掩码值（`[SET] key=<masked>` /
  `[MISSING]`）→ 只报存在性不回显；非 Windows / 缺 config 优雅降级；不进 CI；无新依赖（`tomllib` +
  `subprocess` 均 stdlib，Python 3.13）。

## 5 环境事实（2026-07-16 Intake 核验）

- develop @ `fe50fd3`（#349 flip 合并后）；worktree `maintain/350-s3a-doctor` @ `fe50fd3`（G1 新建）。
- `agents_sync.py` = 635 行、3 模式（`sync` / `--check` / `--adopt`）；docstring L21 + help L550 均标
  「doctor is S3 — not implemented here」/「doctor lands at S3」。
- 仓内**无**既有 `~/.codex/config.toml` 解析代码 → trust 只读需从零实现（`tomllib` stdlib）。
- manifest capability = **37** ≟ on-disk `.claude/skills/` = **37**（canary 当前满足）。
- `setup-mcp-secrets.ps1 -Reload`：逐键 `[SET] key=<masked>` / `[MISSING]` + 「N/M set」汇总，值掩码、只读。
- 反扫「doctor」：需本切片改的 4 行 = `agents_sync.py:21`/`:550` + `sdd/adapters/development-agent.md:94`/`:129`；
  其余命中均为历轮已冻结 plan/intake（不动）。

## 6 Documentation Decision（粗评；Stage 3 已细化）

| Type | Action | 说明 |
| --- | --- | --- |
| INTAKE + PLAN | **Create** | 本对（family 惯例，state: active；merge 后独立 flip PR 翻 completed） |
| adapters/development-agent.md | **Update** | :94「doctor 属 S3」→ 已落地；:129「S3(未落地):doctor+skills gate」→ doctor 落地、skills gate 仍 defer |
| SPEC / ADR / RUNBOOK / GUIDE / STANDARD / ISSUE / ASSESSMENT / CHANGELOG / INDEX | **None** | 工具脚本无新模块接口需 SPEC；ADR-036 D-015 已覆盖；非 user-visible；不进 CI 无 gates.md/ci.yml |

## 7 Owner 拍板记录（2026-07-16，AskUserQuestion）

1. **锚 = C（S3a doctor 只读版）**——候选 B/C/E/A，D 出局（§2）。
2. **范围 = doctor 只读 only**——skills gate blocking flip 留 P4 观察期对齐；memory×5 promotion（议题 1）/
   ssh-manager wrapper（议题 2）/ pg-default（议题 3）各自为锚；不动 ci.yml/gate/protected path。
3. **canary = 保留 unit test + doctor 增补只读报告**（非「迁入」删测）——理由：doctor 不在 CI，删
   `test_dual_discovery_canary_on_disk_matches_manifest` 会把双向 set-equality（CI-blocking）降级为
   dev-machine warning，且 DA060 只护单向（on-disk→manifest）、丢反向（manifest 幻影 capability）。
   Owner 选「无强制损失」。plan `_p1s0` 的「迁入 doctor」措辞据此读作「同时在 doctor 呈现」。

### 7.1 拍板前提溯源纪律（承 [[feedback_wrong_premise_voids_decision|#341 教训]]）

写进 AskUserQuestion 选项的事实断言均 file:line 溯源：canary 双向性 = 测试 :150-152；DA060 单向 =
checker `DA060` 定义；doctor 不在 CI = plan L256「warning-only 不进 CI」。canary 分叉若前提被证伪
（如 DA060 实为双向）则原拍板作废须带更正回 Owner——本切片已核 DA060 确为单向，前提成立。

## 8 Verification Plan

- **Level A（只读）**：`uv run pytest tests/unit -q`（含新 doctor 测试）· `uv run ruff check` ·
  `uv run mypy src/mj_agent`。
- **Level B（本机）**：`uv run python scripts/sdd/agents_sync.py doctor`——实观本机 trust/env/canary 报告。
- **不跑及原因**：integration/smoke（无 biz/LLM 交互，本切片不涉）；doctor 非 CI 面无 gate validator。

## 9 交办事项（本切片范围外，登记以免丢失）

- **skills gate blocking 转正**（V10 warning→blocking）——S3 另一半，plan L315「与 P4 对齐」→ 随 P4
  切片（≥14 日 + 20 run，最早 2026-07-28）走 `ci-blocking-gate-toggle` 逐 gate 独立拍板。
- **#312 议题 1/2/3**（memory×5 promotion / ssh-manager wrapper / pg-default）——各自为锚，未拍板。
- **Developer_Onboarding doctor 提及**（可选）——新 dev 命令；本切片不含，如需另开小 documentation PR。
- **`policies/security.md:72` ADR-034 stale gloss**——已登记 [[[INTAKE]_dual-agent-compat_a6q3-cigates|#347 INTAKE]] §9，非本切片。

## 10 Next Step

Stage 4 Plan 已同批落盘（`[PLAN]_dual-agent-compat_s3a-doctor.md`）→ Stage 5 Plan HITL Gate（锚/范围/canary
三拍板已过）→ Stage 8 实施（`/mj-agent-flow-implement`）。
