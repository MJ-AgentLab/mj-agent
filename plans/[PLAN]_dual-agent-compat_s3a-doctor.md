---
type: plan
slug: dual-agent-compat-s3a-doctor
summary: dual-agent-compat v5 S3a 执行计划——scripts/sdd/agents_sync.py 新增只读 doctor 子命令（① Codex trust 只读报告：tomllib 解析 ~/.codex/config.toml [projects]，精确或仓内祖先匹配，D-015 绝不写 ② HKCU MCP secret env 核对：子进程调 setup-mcp-secrets.ps1 -Reload，值掩码 ③ 双发现 canary 只读报告：on-disk .claude/skills ≟ manifest 37）+ 保留既有 canary unit test（Owner 拍板，非迁入）+ docstring/help/adapter 状态更新 + doctor 写零文件断言测试；退出码 0（报告成）/2（fatal）；warning-only 不进 CI；无新依赖（tomllib/subprocess stdlib）；1 PR，maintain/350-s3a-doctor；不改 ci.yml/gate/.mcp.json/manifest/4 必停面；总锚 #312
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
state: active
version: 1.0
track: shared
related_adrs:
  - decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md
---

# [PLAN] 双工具兼容 v5 — S3a doctor 只读切片（issue #350）

## 1 Linked Artifacts

- Issue：**#350**（本切片）；总锚 **#312**（v5 实施总锚，S3 复选框的 doctor 部分 = S3a）。
- 上游计划：[[[PLAN]_dual-agent-compat|v5 计划]] §S3（L256 doctor 三件套 / L315 S3 收口 / L463·L478·L541
  doctor 只读红线）+ L193（doctor 列为子命令）。
- ADR：[[decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] **D-015**（doctor 只读不写
  trust；Codex trust = 每工程师×每 worktree 人工）+ D-017（A14 surface anchor 覆盖派生面）。
- 同批 [[[INTAKE]_dual-agent-compat_s3a-doctor|INTAKE]]（锚/范围/canary 三拍板记录）。

## 2 Context

`doctor` 是 `agents_sync.py` 最后一个未实现模式（`sync`/`--check`/`--adopt` 已于 S1/S2 落地；
docstring L21/L550 明标「S3 — not implemented here」/「lands at S3」）。它承担全部 **per-machine /
env 检查**——正因需读 `~/.codex/config.toml`、HKCU 变量、shell 出 PowerShell，**与 CI 侧生成器/checker
的「零 env 解析、零网络、fork/clean-clone 不假红」保证冲突** → 故 doctor **warning-only、永不进 CI**
（plan L256）。本切片 = S3 收口的 **doctor 只读子切片**；S3 另一半（skills gate blocking 转正）「与 P4
对齐」留后续，两项独立议题（memory×5 promotion / ssh-manager wrapper）各自为锚。填 P4 等待窗口
（日历腿 2026-07-28 才绑定）的前向进度，且 `scripts/` 工具面完全在 P4 gate 机制外。

## 3 Scope

- **In-scope**：
  1. `do_doctor(repo_root)` + `doctor` 位置子命令（`choices=["sync","doctor"]`）+ 模式互斥更新
     （`sync` XOR `doctor` XOR `--check` XOR `--adopt`）。
  2. Trust 只读报告（§4.3a）· HKCU env 核对（§4.3b）· canary 只读报告（§4.3c）。
  3. docstring（L21 模式表 + L40-45 纯变换声明加 doctor 机器面例外）+ help（L550）去「lands at S3」。
  4. doctor 写零文件断言 + 退出码 + 优雅降级测试（`tests/unit/test_sdd_development_agent.py`）。
  5. `sdd/adapters/development-agent.md:94/:129` 状态更新。
  6. 本 `[INTAKE]+[PLAN]` 对。
- **Out-of-scope**（各自独立，不在本 PR）：skills gate blocking 转正（→ P4 对齐）· memory×5 promotion
  `project-with-adr`（议题 1）· ssh-manager wrapper（议题 2）· pg-default 单一真相（议题 3）· 任何
  `ci.yml`/gate 姿态变更 · 对 trust / protected path / `.mcp.json` / manifest 的**任何写入** ·
  既有 canary unit test 的删除/迁移（Owner 拍板保留）。

> **纵切片归属**：本切片是 S3 的自身可验、可独立 review-合的窄完整路径（doctor 只读）。S3 余项
> `blocked-by` P4 观察期或各议题独立拍板，另行成片。

## 4 Design

### 4.1 CLI 形态

`command` 位置参数 `choices=["sync","doctor"]`（doctor 与 sync 同形，承 plan L193 子命令口径，非
`--doctor` 旗标）。模式互斥（main:575）改为四元：`[cmd=="sync", cmd=="doctor", args.check, args.adopt
is not None]`，`sum != 1 → exit 2`。`--surface` 仍仅配 `--check`（doctor 传 `--surface` → exit 2，
沿用既有校验风格）。

### 4.2 退出码（doctor）

- **0** = 报告已产出（**含 warning 仍 0**——warning-only，doctor 是诊断非 gate）。
- **2** = fatal：manifest 不可读 / 复用既有 `FatalCheckError` 通道（main:629-631）。
- warning（trust 未信任 / env 缺失 / canary 漂移）**打印但不改退出码** → 与 plan「warning-only」一致，
  也保证 doctor 永不因本机状态令任何脚本失败。

### 4.3 三项只读检查

**(a) Codex trust 只读报告**——`tomllib.load(~/.codex/config.toml)`；取 `[projects]` 表；判断
**当前仓根或其仓内祖先**是否有受信条目（S2 spike ③ 语义：精确匹配或仓内祖先，容器条目覆盖全 worktree）。
报告当前根的 TRUSTED / UNTRUSTED + 授予信任的条目路径。**绝不写**该文件（D-015 红线）。缺文件 →
报「no ~/.codex/config.toml（untrusted；见 onboarding 手工 trust 步骤）」。**只报当前根状态**，不回显
其他 project 路径 / 任何 MCP·secret 内容（隐私 + 数据边界）。
> **Stage 8 spike（已做，2026-07-16 本机 `~/.codex/config.toml` sanitized 读实证）**：
> 格式 = `[projects.'<path>']` 表 + `trust_level = "trusted"`（TOML → `config["projects"]` dict）。
> 路径键为 **Windows 反斜杠**，部分带 `\\?\` 扩展前缀、**盘符大小写混用**（`D:` vs `d:`）→ 匹配须
> 规范化（casefold + 分隔符统一 + strip `\\?\`）。容器条目 `d:\…\projects\mj-agent` 受信 → 经**祖先遍历**
> 覆盖全 worktree（证 S2 spike ③；本 worktree 即由该祖先获信）。实现：规范化当前根 + 全部祖先，
> 逐一测受信集成员，报首个命中条目；仓根用注入 `repo_root`，祖先遍历止于文件系统根。

**(b) HKCU MCP secret env 核对**——Windows 上子进程 `powershell -NoProfile -File
.claude/scripts/setup-mcp-secrets.ps1 -Reload`。非 Windows（`platform.system() != "Windows"`）/ 缺
PowerShell / 缺脚本 → 报「N/A」，不崩、不改退出码。**绝不回显 secret 值**（doctor 不自解密、不读
`.enc`）。两处 **Stage 10 实机核验修正**（本机跑出，非计划外扩范围，均属 AC「presence only」加固）：
> **① 捕获 bytes 非 text**——`-Reload` 控制台输出非可靠 UTF-8（Windows codepage），`text=True` 的
> reader 线程会因非法续字节崩溃且 `stdout=None` → `AttributeError`。修 = `capture_output=True`（bytes）
> + `decode("utf-8","replace")`；`[SET]/[MISSING]/[Done]` 标记本就 ASCII，末端再 ASCII 强制。
> **② presence-only 再脱敏**——`-Reload` 的 `Format-MaskedValue` 显示值**前 4 字符**（口令即
> `Ming****` = 部分泄密）。doctor 只保留 `[` 开头状态行且**剥去 `= <masked>` 片段** → 只报存在性
> `[SET] KEY` / `[MISSING] KEY`，不回显任何值片段。回归测试 `test_doctor_env_tolerates_non_utf8_
> powershell_output` 双证（不崩 + `Ming` 不入报告）。

**(c) 双发现 canary 只读报告**——数 on-disk `.claude/skills/*/SKILL.md` ≟ manifest capability 计数
（当前 37≟37）。相等 → INFO「N≟N」；漂移 → WARN（列缺失/多余方向）。**只读、不改退出码**。
**保留**既有 `test_dual_discovery_canary_on_disk_matches_manifest`（Owner 拍板；doctor 报告是增补面，
非替代——doctor 不在 CI，删测会把双向 set-equality 从 CI-blocking 降级为 dev-machine warning）。

### 4.4 与 CI-纯模式的隔离

doctor 是机器感知的**唯一例外**；`sync`/`--check`/`--adopt` 保持零 env/网络。`tomllib`/`subprocess`/
`platform`/`os.environ` 仅在 `do_doctor` 路径引用；模块顶层 import 保持不引入运行期副作用（`tomllib`
顶层 import 无害）。CI 从不调 `doctor` 子命令 → V10/V11/Tests step 行为零变化。

### 4.5 输出规约

**ASCII-only**（#318 教训：Windows 控制台或非 UTF-8）；分节 `TRUST` / `ENV` / `CANARY`，逐行
`[PASS]`/`[WARN]`/`[INFO]`/`[N/A]` 前缀；末尾一行汇总。不含 emoji/中文（脚本输出面）。

## 5 收窄的真实影响（不夸大、不缩小）

- **加**：一个只读 dev 诊断子命令。**不加/不减任何强制**——canary unit test 原样保留、无新 CI gate。
- **不动**：运行期（`src/mj_agent/**` 零改）· CI（`ci.yml`/gates 零改）· 投影产物（`.agents/**` /
  `.codex/config.toml` 零改）· `.mcp.json` / manifest（只读）· 4 必停面。
- 唯一行为变化 = 新增 `agents_sync.py doctor` 子命令；`sync`/`--check`/`--adopt` 行为逐字不变。

## 6 Work Breakdown（1 PR，`maintain/350-s3a-doctor`）

| # | 文件 | 改动 |
| --- | --- | --- |
| W1 | `scripts/sdd/agents_sync.py` | `do_doctor` + `doctor` 子命令 + 模式互斥四元 + docstring L21/L40-45 + help L550 |
| W2 | `tests/unit/test_sdd_development_agent.py` | doctor 测试：写零文件 / 健康树 exit 0 / 缺 config 优雅 / 非 Windows env=N/A / trust 只读不写（temp HOME）/ 既有 canary 测试仍在 |
| W3 | `sdd/adapters/development-agent.md` | :94 + :129 状态更新（doctor 落地；skills gate 仍 defer） |
| W4 | `plans/[INTAKE]+[PLAN]_dual-agent-compat_s3a-doctor.md` | 本对（state: active） |

红→绿 commit 序：先 W2 加失败/占位测试 → W1 实现转绿 → W3/W4 文档。

## 7 Verification

- `uv run pytest tests/unit -q`（含新 doctor 测试 + 既有 canary/V8/V9 测试全过）
- `uv run ruff check` · `uv run mypy src/mj_agent`（mypy 面为 src/；脚本改动由 ruff + 测试覆盖）
- 手动 `uv run python scripts/sdd/agents_sync.py doctor`（本机实观 trust/env/canary；退出码 0）
- 结构性防呆：本机带 `.env` 跑 unit 有 [[project_prod_repoint_local_env|#298]] 2 假红，clean worktree 不受影响。

## 8 验收标准（全部可执行自证；承 [[feedback_wrong_premise_voids_decision|#341/#344]]「AC 逮住作者本人」教训）

- [ ] **AC-1**（docstring 去 stale）：`grep -cE "not implemented here|lands at S3" scripts/sdd/agents_sync.py` = **0**。
- [ ] **AC-2**（模式互斥）：`uv run python scripts/sdd/agents_sync.py doctor --check` 退出 **2**（两模式）；`… doctor --surface skills` 退出 **2**。
- [ ] **AC-3**（写零文件，D-015 核心）：测试断言 `do_doctor` 前后 worktree + `$HOME/.codex` 文件集合不变（含 `~/.codex/config.toml` mtime 不变 / temp HOME 无新文件）。
- [ ] **AC-4**（健康树）：`uv run python scripts/sdd/agents_sync.py doctor` 退出 **0**；stdout **纯 ASCII**（`python -c "…assert out.isascii()"` 或测试内 `.isascii()`）。
- [ ] **AC-5**（trust 只读+降级）：缺 `~/.codex/config.toml` 时报 UNTRUSTED 且退出 0；trust 检查从不写该文件（AC-3 覆盖）。
- [ ] **AC-6**（env 降级）：非 Windows / 缺 PowerShell 时 ENV 段报 `[N/A]`、不崩、退出仍 0。
- [ ] **AC-7**（canary 增补非替代）：doctor CANARY 段报 `37≟37`；`grep -c "def test_dual_discovery_canary_on_disk_matches_manifest" tests/unit/test_sdd_development_agent.py` = **1**（既有测试仍在）。
- [ ] **AC-8**（回归）：`uv run pytest tests/unit -q` 全绿 · `uv run ruff check` 无违规 · `uv run mypy src/mj_agent` 通过。
- [ ] **AC-9**（adapter 同步）：`grep -cE "doctor 属 S3|S3（未落地）.*doctor" sdd/adapters/development-agent.md` = **0**（两 stale doctor 行已更新；pattern **anchored to `doctor`** 以免过匹配合法 V10「转正属 S3/P4」行——5-lens 对抗审查 2026-07-16 逮到原 `属 S3` 裸模式假失败）。

## 9 Risks / Anti-goals

- **D-015 供应链洞**（doctor 写 trust）：mitigate = 只读构造 + AC-3 写零文件断言 + 代码评审（F3）。
- **secret 回显**：mitigate = `-Reload` 掩码 + 只报存在性 + doctor 不自解密（不碰 `.enc`）。
- **跨平台**：mitigate = `platform.system()` 分支 + 非 Windows env=N/A + 缺 config/脚本优雅降级。
- **Anti-goal**：不碰 `.mcp.json`（A14）/ manifest / emitter B 投影逻辑（D-017 语义面）/ 任何 gate 姿态；
  不删既有测试。（注：编辑 `agents_sync.py` **本身**在 `mcp-server-trust-posture-change` D-017 surface
  anchor 内——见 §10；本切片只加只读 `doctor`，不动投影/posture。）
- **CI 污染**：mitigate = doctor 永不进 `ci.yml`；机器面 import 仅在 `do_doctor` 路径生效。

## 10 Owner Gates

- **锚 / 范围 / canary 三拍板**已过（[[[INTAKE]_dual-agent-compat_s3a-doctor|INTAKE]] §7）。
- commit / push / PR 创建 / merge = `OWNER_APPROVAL_REQUIRED`（逐一交 Owner）。
- **无** §3.1 专属 4 必停触发（不动 skills/system.md/qcm_catalog/SQL guardrail）；**无** A14（`.mcp.json` 不改）；无 `.env`/secrets 写。
- **D-017 触发（更正 2026-07-16；原本节误标「无 D-017」）**：`scripts/sdd/agents_sync.py` 在
  `mcp-server-trust-posture-change` surface anchor 内（上游 plan L521/L543 ·
  [[decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]] D-017 · `policies/ai-agent.md` §4 L94），
  故**编辑本文件即必停面**。本切片仅加**只读 `doctor` 诊断**，不改 emitter B / MCP 投影 / trust posture /
  `codex.posture` 段——非语义 trust 变更、纯 surface-match。由 Owner 切片拍板（锚 C + 范围 + commit/push/PR
  授权）满足 D-017 Owner HITL；**动作面未扩，属 correctness 更正非决策反转**（承
  [[feedback_wrong_premise_voids_decision|错误前提纪律]] + #347 判例）。

## 11 Next Step

Stage 8 实施（`/mj-agent-flow-implement`）：W2→W1→W3→W4 红→绿 → Stage 10 verify → Stage 11 self-review
（大改用 5-lens 对抗审查）→ commit/push/PR 交 Owner → merge 后 flip PR 翻 state completed。
