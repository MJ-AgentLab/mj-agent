---
type: sdd-adapter
artifact: development-agent
state: active
version: 1.0
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-14
track: engineering-workflow
ai_visibility: source-of-truth
---

# Adapter: Development Agent (dual-tool compatibility)

> dual-agent-compat v5 P1 落地（#320 / ADR-036）——本 adapter 吸收 Claude Code 与 Codex 的
> **入口、审批载体与调用差异**；它不拥有业务规则，也不是第二事实源（program plan
> [[../../plans/[PLAN]_dual-agent-compat|v5]] §7 层级：本文件属「派生清单/平台适配」层，
> canonical 规则只在 kernel——`sdd/` + `policies/` + capability contracts）。
> 机器可读侧 = [[../development-agent|sdd/development-agent.yml]]（manifest，唯一覆盖状态 SoT）。

## §Scope

**Included**：

- `sdd/development-agent.yml` — 37 项 in-tree skill 能力的双工具覆盖 / 审批 / 证据索引 +
  `projection` 三档（D-014 白名单 SoT）+ `mcp` per-server 三档（D-013）+ `codex.posture` 手写段
- 双工具行为矩阵（同一 canonical 停点的 per-tool 载体，见 §Behavior Matrix）
- 根 + 4 嵌套 `AGENTS.md` 与同层 `CLAUDE.md` `@AGENTS.md` 引用关系（V8 校验面）
- 投影域结构规则（引用闭包 / reconcile / lock + S2 #330 起 codex-config PJ04x；V9 校验面）
- `.codex/config.toml` 生成产物与 MCP emitter B 的 gate/CLI 契约（S2 #330 落地：3 spikes 全 PASS +
  Owner 进拍板 2026-07-14；语义治理契约见根 `AGENTS.md`「Generated projections」节）

**Excluded**：

- 各 skill 的语义正文（canonical 在 `.claude/skills/*/SKILL.md`，由 claude-code-skill adapter 治理）
- in-source runtime canonical（→ runtime-skill / prompt adapters）
- `.mcp.json` 本体（A14 保护面；本 adapter 只消费其 server 清单事实）
- 投影产物的语义正文（`.agents/skills/**` 是 `agents_sync.py` 生成的字节同一副本——S1 已落地，
  治理契约见根 `AGENTS.md`「Generated projections」节；本 adapter 只登记其 gate 与 CLI 契约）

## §Behavior Matrix（同一停点，per-tool 载体）

停点本身 tool-neutral（`OWNER_APPROVAL_REQUIRED`，canonical 10-enum per
[[../../policies/ai-agent|policies/ai-agent]] §4 + AGENTS Git Owner gate）；只有载体不同：

| 面 | Claude Code 载体 | Codex 载体 |
|---|---|---|
| 4 项专属必停（runtime×3 + guardrail） | settings `ask` 逐写拍板门 + harness prompt | `AGENTS.md` 自守 prose（boundary 3） |
| Git Owner gate（commit/push/pr-create/merge） | 会话内 Owner 明示批准（ADR-034） | 同左（AGENTS.md boundary 4） |
| G1/G2 Git 纪律 | fail-closed PreToolUse hook（`guard-git-workflow.ps1`） | `AGENTS.md` boundary 5 自守 |
| 数据边界（ADR-006/009） | 4-tool 链 + L1/L1b guardrail + RO role | 同一链；`AGENTS.md` boundary 1 自守 |
| Secrets 边界 | permissions deny + sanitized 脚本缝 | `AGENTS.md` boundary 2 自守 |
| 同层局部约束 | 嵌套 `CLAUDE.md`（`@AGENTS.md` 导入） | 嵌套 `AGENTS.md`（root→cwd 逐级发现） |
| 程序性确认（AskUserQuestion 等） | harness 原语 | 会话对话等价（非 Owner 门；manifest `approval.mode: none`） |

## §Standards（manifest 契约摘要；全文 = program plan §9，checker 逐条执行）

> **V8 规则声明锚**：以下由 `scripts/sdd/check_development_agent.py` 机器校验。

- 顶层必含 `schema_version` / `snapshot` / `owners` / `capabilities`；未知 `schema_version` 拒绝。
- capability 必含 `id` / `group` / `required` / `claude` / `codex` / `evidence`；`id` 全仓唯一且
  对应 `.claude/skills/<id>/` 在盘存在。
- 每侧三正交字段：`support_mode`（5 枚举）/ `approval`（`{mode, gates}`）/ `enforcement`（5 枚举 list）。
- `approval.mode: none` ⇒ `gates: []`；`owner-hitl` ⇒ ≥1 gate 且 `policy_ref` ∈ canonical 10-enum
  ∪ `agents-git-owner-gate`；gate 必含 `policy_ref/trigger/stop_before/evidence_required`。
- `required: true` 双侧均不得 `unsupported`；`unsupported` 仅限 `required: false` 且
  approval none + enforcement 空；其余 support_mode 要求 enforcement 非空。
- `adapter-backed` 必带 `adapter_ref` 指向本文件；`script-ci` 的 evidence 须含可在 clean clone
  运行的仓内脚本或 CI job。
- `projection` ∈ project / after-neutralization / never（D-014：投影副本不计入 37 计数 SoT）；
  `mcp.servers.*.projection_policy` ∈ project / project-with-adr / never（D-013：biz×5 +
  ssh-manager 永 never）。
- 禁 `owner_agent` / 工具专属固定职责字段；统计（37 等计数）只由 manifest 派生，正文不再作 SoT。
- 根 + 4 嵌套 `AGENTS.md` 存在且同层 `CLAUDE.md` 含 `@AGENTS.md` 导入（V8 结构面）。

> **V9 规则声明锚**：以下由 `scripts/sdd/check_agents_projection.py` 机器校验。

- **引用闭包**：`projection: project` 技能 SKILL.md 的 `## Handoff*` 段 `/mj-agent-*` 出边必须
  ∈ project 集（`.agents/` 未落地时降 warning——S0 空态；产物出现后 error）。
- **全量 reconcile**：`.agents/skills/` 现存目录 ≟ manifest project 集；多出/缺失 = FAIL；
  `.agents/` 不存在 = vacuous pass（S0 空态不假红）。
- **lock 一致性**：`.agents.lock.json` ↔ 产物 `body_sha256`（LF 归一 canonical 算法，复用
  `scripts/sdd/_common/frontmatter.py`）；两者均缺 = pass，仅一方存在 = FAIL。

> **V10 规则声明锚（S1 #326）**：以下由 `scripts/sdd/agents_sync.py --check` 机器校验
> （regenerate-and-diff；一切内容比较 LF 归一——`.md` 未 eol-pin、Windows/ubuntu 检出 EOL 不同）。

- **产物 ↔ 源一致**：`.agents/skills/<name>/SKILL.md` 与 `.claude/skills/<name>/SKILL.md`
  LF 归一后相等（手改产物或改源未重跑 `sync` 均红，文案给规定动作 per D-012）。
- **README ↔ 固定模板一致**；**lock ↔ 重算值一致**（排序单行条目）；`.agents/` 树内不得有
  期望集之外的文件/目录（与 V9 reconcile 互补：V9 对账目录集，V10 对账内容与杂散文件）。
- **生成器 CLI 契约**：`sync`（幂等全量再生成 + 孤儿清理）XOR `doctor`（S3a #350；只读
  per-machine trust/env/canary 报告，warning-only，永不进 CI，写零文件 per D-015）XOR
  `--check`（只读）XOR `--adopt <name>`（显式反灌 + 自动 realign；Owner HITL 适用于源写入）；
  退出码 0/1/2。`sync`/`--check`/`--adopt` 生成期零 env 解析、零网络（fork/clean-clone 不假红）；
  `doctor` 是机器感知例外（读 trust/env，从不进 CI）。

## §CI Gate

| Gate | 脚本 | 阻塞模式（真值） |
|---|---|---|
| V8 | `scripts/sdd/check_development_agent.py --all --fail-on error` | **warning**（P1 首发 `continue-on-error: true`；P4 观察期满 + Owner 批准后按 `ci-blocking-gate-toggle` 流程翻转） |
| V9 | `scripts/sdd/check_agents_projection.py --all` | **warning**（同上；MCP 产物面 day-1 blocking 由 V11 独立承载 per D-016，执行记录 #330） |
| V10 | `scripts/sdd/agents_sync.py --check --surface skills` | **warning**（S1 首发 #326；skills 面沿 warning→blocking 惯例 per D-016，转正属 S3/P4；S2 #330 起 CI 调用收窄 skills 面）。真值注记：`test_agents_sync.py` 真实树钉线令同一不变量经 blocking Tests step 事实硬约束（V8/V9 钉线同族先例） |
| V11 | `scripts/sdd/agents_sync.py --check --surface mcp` | **blocking（day-1 per D-016，不设 warning 观察期；`ci-blocking-gate-toggle` Owner 执行记录 = #330 comment 2026-07-14）**。真值注记：`test_real_tree_mcp_projection_in_sync` 钉线双保险 |

单测：`tests/unit/test_sdd_development_agent.py`（含双发现 canary：on-disk `.claude/skills/`
目录数 ≟ manifest 计数）+ `tests/unit/test_agents_sync.py`（幂等 / drift 三态 / reconcile 负向 /
跨 EOL golden / `--adopt` / V9 集成 / 真实树钉线）。注册：[[../gates|sdd/gates.md]] §2。

## §Current Implementation Status

- P1+S0（#320）：manifest + V8/V9 checker + 单测 + canary 落地；CI warning 首发。
- S1（#326）：白名单定案全 5（闭包收口，V9 0E/0W）+ `agents_sync.py`（sync/--check/--adopt）+
  🟢 首批 5 投影 + `.agents.lock.json` + `.agents/README.md` + drift gate V10 warning 首发 +
  根 AGENTS.md「Generated projections」契约条。Codex 实机发现验证依赖 Owner trust（D-015），
  post-merge 配合执行。
- S2（#330）：3 spikes 全 PASS（env_vars 按名透传 / trusted 仓级实载 / worktree 发现语义）→
  emitter B（`.codex/config.toml`：github/playwright/serena+`--context codex` 三 project 档 +
  `env_vars` 按名 + posture 转写）+ lock 保留键 `.codex/config.toml` + V9 PJ040-PJ045 +
  MCP gate V11 day-1 blocking + G7 内容扫描扩展。spike 证据：vault + #330 comment。
- P3（#337）：第二批四 flow skills（scope-drift/self-review/review-respond/post-merge）manifest
  `evidence` 收口 + S6（flow-post-merge，`report-schema-exact`）双工具 clean-clone 实跑
  Claude ×2 + Codex ×2 **4/4 PASS**（复用冻结 P2 harness，零改动）+ **剩余 A/B/C 映射确认**：
  全 37 项 `projection` 三档已 = program plan §4.4 终态 🟢5/🟡21/🔴11——🔴11
  （`doc-validate`/`flow-verify` script-ci 等价 · `git-issue` gh CLI 等价 · 8 冻结 `infra-*`）为
  「已有普通脚本/文档/CI 等价通道的便利型技能，不强制迁移」；🟡21 各自前置未闭前不投；P3 无新增
  强制迁移，S1 已投 🟢5 不变。诚实覆盖：post-merge←S6 专属 fixture / self-review←S2·S3 传递 /
  scope-drift(9)·review-respond(15)←本 §Behavior Matrix 推理覆盖（无专属 fixture，不伪造）。
  证据 `evidence/development-agent-p3/SUMMARY.md`；达成 §11.1 P3→P4 晋级门（S1–S6 两工具各 2×）。
- S3a（#350）：`agents_sync.py doctor` 只读落地——Codex trust 只读报告（`~/.codex/config.toml`
  `[projects]`，精确/仓内祖先匹配，D-015 绝不写）+ HKCU env 核对（`setup-mcp-secrets.ps1 -Reload`，
  值掩码）+ 双发现 canary 只读报告；warning-only，永不进 CI。既有 canary unit test **保留**（Owner
  拍板：doctor 报告是增补面，非「迁入」删测——doctor 不在 CI，删测会把 CI-blocking 双向 set-equality
  降级为 dev-machine warning）。
- S3 余项（未落地，与 P4 对齐）：skills gate（V10）blocking 转正 + 两项独立拍板议题
  （memory×5 promotion / ssh-manager wrapper）。
