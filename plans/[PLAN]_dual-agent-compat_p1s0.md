---
type: plan
summary: 双工具兼容 v5 P1+S0 执行计划（issue #320）——薄适配骨架（manifest/checker/嵌套 AGENTS.md）+ 投影基建（projection 字段/投影 checker/canary/.claudeignore）+ ADR-036，stacked 3-PR 链；含 Stage 3 repo-scan 4 项设计裁定与 7 项 Owner 拍板记录
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-13
state: active
track: shared
---

# [PLAN] 双工具兼容 v5 — P1+S0 执行计划（issue #320）

## 1. Linked Artifacts

- Issue: #320（P1+S0 执行）· 总锚 #312 · Program plan: [[[PLAN]_dual-agent-compat|v5 计划]]（§8 目标文件 / §9 manifest 契约 / §10 checker 接口 / §11 分阶段 / §11.1 晋级条件）
- Intake: [[[INTAKE]_dual-agent-compat_p1s0|Stage 0 Intake]]（2026-07-13）
- Repo Scan: Stage 3 对话输出（2026-07-13，6 维并行扫描；证据行号以 develop @ `f2850fa` 为基准）
- 关联 ADR：[[../decisions/ADR-035_Codex_Full_Development_Participant|ADR-035]]（双工具授权基础）· **ADR-036 本切片立**（收 D-001~D-017，PR-3）
- Owner 拍板记录（2026-07-13，Stage 0 四项 + Stage 5 三项，共 7 项）：
  1. 单执行 issue #320 + 落盘 INTAKE（§2.1 触发：多 PR 链 + HITL≥3）
  2. **D-017 anchor 扩展随本切片落地**（ai-agent.md §4 + PR 模板，不等 S1/S2）
  3. S0 双发现 canary 以 **unit test 承载**（S3 迁入 doctor）
  4. PR 拆分粗方向 stacked 3-PR，自底向上合并
  5. 执行计划整体批准（含闭包 Handoff 窄定义 + 空态降级、§10 CLI 自建族、嵌套 AGENTS.md 治理注册、gates.md V8/V9 注册；state flip 按 #319 先例 post-merge 另开小 PR）
  6. manifest `required: true` 集合 = **闭环主路径 18 项**（flow×10 + git×7〔branch/commit/push/pr/sync/delete/issue〕+ doc-validate）
  7. `codex.posture` 初值 = `approval_policy: on-request` + `sandbox_mode: workspace-write` + `project_doc_max_bytes: 65536`（初值随 PR-2 review 再确认一次；该段后续修改必停）

## 2. Context

P0（#313）已闭环且遗留口径比预期干净：PR 模板 canonical 10-enum 已对齐（PULL_REQUEST_TEMPLATE.md:61-72）、35/34P 旧计数零残留——PR-3 无历史包袱。manifest/checker 是 P2 起 skills 端到端与 S1 投影机制的机器 SoT 前置；`.codex/**` / `.agents/**` 保护面缺口（program plan §3 点名）由 D-017 anchor 扩展提前闭合。

风味判定：全切片不触 `src/mj_agent/**`（无 B 风味）、不触 `.claude/**` / `.mcp.json`，全部为 C（sdd 文档 / scripts / tests / CI / 治理文档 / 根级入口文件）。§3.1 必停 4 项（trigger 10-13）均不触发；High 风险来自 CI workflow 变更、manifest `mcp`/`codex.posture` 受保护邻接面创建、ADR-036 治理文档。

Stage 3 repo-scan 4 项设计裁定（已随 Stage 5 拍板）：

1. **闭包 = Handoff 窄定义 + 空态降级**：🟢5 候选 body 含指向非白名单技能的 `/mj-agent-*` 引用（如 git-push→git-pr）；若按「全部引用」算闭包，首批白名单缩为空。按 program plan 字面「Handoff 出边」窄定义——仅 `## Handoff*` 段出边须 ∈ projection=project 集；`.agents/` 不存在（S0 空态）时闭包违规降 warning，产物出现（S1+）转 error。S1 定白名单时以 checker 输出定案（§4.4「最终取 3-5 个，以引用闭包 checker 核验为准」）。
2. **§10 CLI 自建族**：`--all/--changed-from` XOR + `--json` + `--fail-on` + 退出码 0/1/2 与现有 `_common/cli.py`（`--all/--strict`，Summary.exit_code）不同族——新 checker 自建 argparser，仅复用 `_common` 的 frontmatter/yaml_io 底层；沿用 `main(argv=None, repo_root=None)` 注入模式（#217 教训；先例 check_capability_impact.py:296）。
3. **嵌套 AGENTS.md 治理注册**：documentation.md §2.6 例外条款现仅覆盖根文件——扩展至嵌套 AGENTS.md（无 frontmatter / A1-A3 不适用 / A4+A6 适用 / archive sweep 覆盖）+ §4 Review Cadence 清单加行。
4. **gates.md 注册**：两 checker 挂 V8（check_development_agent）/ V9（check_agents_projection）注册于 §2 adapter validators 表（下一空位），真值如实登记 warning（P1 首发）；随 ci.yml 同 PR（PR-3）落。

## 3. Scope

- 包含：program plan §8 P1 全部目标文件 + §11 S0 全部条目 + ADR-036 + D-017 anchor 扩展三落点 + 嵌套 AGENTS.md 治理注册
- 不包含：`agents_sync.py` 与任何投影产物（S1）；MCP emitter / 3 spike（S2）；doctor（S3）；`.mcp.json`；CI blocking flip；`.claude/**`（含 SKILL_INDEX 计数改写——统计漂移由 checker warning 报告）；`tests/fixtures/development-agent/scenarios/S1-S6`（P2 起）；#312 登记 4 项独立拍板议题
- 前置依赖：P0 已 merge（develop @ f2850fa）；PR-2 base = PR-1 分支，PR-3 base = PR-2 分支（stacked，自底向上依序合并，防 #314/#315 事故）

## 4. 任务拆解（Stage 8 编号 · 全部风味 C）

### PR-1 `maintain/320-p1s0-agents-entry`——入口对等：嵌套 AGENTS.md + @引用 + 治理注册 + plans 落盘

- **8a 嵌套 AGENTS.md ×4**：`capabilities/AGENTS.md`（能力目录局部约束：contracts 冻结面、evidence 规范、可见性入口）· `docker/AGENTS.md`（安全边界：compose.prod A14 邻接、`--env-file` 语义〔docker 进程解析非 Agent 读取〕、secrets 不入仓）· `src/mj_agent/AGENTS.md`（4 项专属必停面清单 + propose→拍板→apply + ADR-006/009 数据边界指针）· `tests/AGENTS.md`（fixtures 纪律、conftest skip 约定、tests/bdd 分带、外部依赖边界）。内容规则：工具中立；只指针 kernel（`sdd/` + `policies/` + capability contracts）不复制规则正文（§2.6 代偿纪律）；**无 frontmatter、无 wikilink**（Codex 直读；用 backtick 路径 / 相对 md 链接）；每份 ≤60 行；素材源 = 同层 CLAUDE.md 主题（不复制其 Claude 专属命令面）。
- **8b 根 AGENTS.md 增量**：新增「Nested AGENTS.md map」小节（4 入口清单 + 一句定位）+ 更新 footer 注记；不重构 P0 已 de-primary 的既有段落。
- **8c CLAUDE.md `@AGENTS.md` 引用 ×5**：根 CLAUDE.md 头部指针段（L3-4）后加 `@AGENTS.md` 导入行 + 一句说明；4 嵌套 CLAUDE.md 各加同层 `@AGENTS.md` 导入行（additive-load 语义下同层规则对 Claude 可见）。不复制 AGENTS.md 正文。
- **8d 治理注册**：documentation.md §2.6 AGENTS.md 例外条款扩至嵌套（root + 4 subdir 同待遇）+ §4 Review Cadence 清单加「AGENTS.md（root + 4 subdir）」；policies/archive.md:140 sweep 根文件清单核对，仅在陈述变假处最小更新。
- **8e plans 落盘**：`[INTAKE]_dual-agent-compat_p1s0.md` + 本文件（随本 PR 携带）。

### PR-2 `maintain/320-p1s0-manifest-checker`（base=PR-1）——机器 SoT：manifest + adapter + 双 checker + 单测

- **8f manifest `sdd/development-agent.yml`**：`schema_version: 1` + `snapshot` + `owners` + `capabilities` 37 条目（`id` 用完整 canonical 名；`group` = doc/flow/git/infra/runtime）。claude 侧 `support_mode` 全 native（`enforcement` 按实况：settings ask / PreToolUse hook → `native-permission`，其余 `manual`）；codex 侧按 §4.1-4.3 A/B/C 映射（native ×1〔flow-diagnose〕/ adapter-backed ×18〔B 组〕/ script-ci 或 manual ×18〔C 组〕）。`approval` 仅记 Owner 门：runtime-biz-catalog-sync→`biz-catalog-sync`、runtime-prompt-version-bump→`prompt-version-or-body-change`、runtime-skill-doc-improve→`runtime-skill-content-change`（stop_before: write）；git-commit/push/pr→AGENTS Git Owner gate（stop_before: commit/push/pr-create，evidence: explicit-owner-message）；runtime-eval-baseline 的 AskUserQuestion 为程序性确认非 Owner 门→`approval.mode: none`。`required: true` = 拍板 18 项集合。`projection` 三档初值 🟢5/🟡21/🔴11（§4.4）。`mcp` 段 14 servers per D-013：github/playwright/serena=`project`（serena 注记 `--context claude-code`→codex transform，.mcp.json:17）、pg-mj-agent-memory-*×5=`project-with-adr`、pg-mj-system-biz-*×5 + ssh-manager=`never`。`codex.posture` = 拍板初值（on-request / workspace-write / 65536）。禁 `owner_agent` / 工具专属职责字段。
- **8g adapter doc `sdd/adapters/development-agent.md`**：9-field frontmatter 家族式（`type: sdd-adapter`）；§Scope / §行为矩阵（同一 canonical 停点的 per-tool 载体：Claude=harness ask/hook prompt，Codex=AGENTS.md 自守 prose）/ §Standards（§9 契约的 adapter 侧摘要，声明规则不复制 canonical 正文）/ §CI Gate（V8/V9 指针，真值 warning 首发）。
- **8h checker `scripts/sdd/check_development_agent.py`**：§10 接口逐字——`--all` XOR `--changed-from <ref>`（缺失/并给/坏 ref → exit 2）、`--json`（顶层固定 `schema_version/mode/base/violations/summary`；violation 含 `code/severity/capability_id/path/message`；stdout 纯 JSON）、`--fail-on error|warning` 默认 error、退出码 0/1/2。规则：schema/enum 校验（未知 `schema_version` → exit 2）；required 两侧覆盖（unsupported=error）；文件/evidence 引用存在性；重复 id；**根+嵌套 AGENTS.md 存在性 + 同层 CLAUDE.md 含 `@AGENTS.md`**；canonical 10 计数（ai-agent.md §4 表 =10 行且 PR 模板 checkbox =10）；统计一致（manifest 计数 ≟ on-disk `.claude/skills/` 目录数 ≟ SKILL_INDEX 宣称值；drift=warning）。`main(argv=None, repo_root=None)` 注入式。
- **8i checker `scripts/sdd/check_agents_projection.py`**：同族 CLI；三类规则——闭包（projection=project 技能 SKILL.md 的 `## Handoff*` 段 `/mj-agent-*` 出边 ∈ project 集；`.agents/` 不存在时 severity=warning，存在时 error）、reconcile（`.agents/skills/` 现存目录 ≟ manifest project 集；多出/缺失=error；`.agents/` 不存在=vacuous pass）、lock（`.agents.lock.json` ↔ 产物 body_sha256〔复用 `_common/frontmatter.py` canonical 算法〕；两者均缺=pass，仅一方存在=error）。**当前空态（无 .agents/ 无 lock 无 .codex/config.toml）exit 0 不假红**。
- **8j 单测 `tests/unit/test_sdd_development_agent.py`**：真实树 `--all` pass 钉线 + tmp_path 合成 fixtures 负例矩阵（未知 schema_version→2、未知枚举→1、required unsupported→1、canonical 引用失效→1、`--all`+`--changed-from` 并给→2、坏 ref→2、非必需证据缺失→warning 且 `--fail-on warning` 时→1、投影三规则正/负例〔空态 pass、多出文件 FAIL、lock 不一致 FAIL、Handoff 出边闭包〕）+ **双发现 canary**（on-disk 37 ≟ manifest ≟ SKILL_INDEX 宣称值）。
- **8k `.claudeignore`** 加 `.agents/` 行（注释注明 D-012 生成产物 + F9 应急开关语义）。

### PR-3 `maintain/320-p1s0-ci-adr036`（base=PR-2）——门禁接入 + 决策收口

- **8l ci.yml + gates.md**：dual-agent block（ci.yml:283 后、Tests 前）2 steps——`check_development_agent.py --all --fail-on error` 与 `check_agents_projection.py --all`，均 `continue-on-error: true`（warning 姿态首发）+ :261-263 式惯例注释（blocking flip 另走 `ci-blocking-gate-toggle`）；sdd/gates.md §2 注册 V8/V9（真值 warning）。
- **8m ADR-036**：`decisions/ADR-036_*.md`（TEMPLATE_ADR 9 字段 + tags，ADR-035 式）；收 D-001~D-017 逐条 id + 一句（指针 program plan §18 不复制全文）；Alternatives = 外部 kernel / 第三方同步器（Ruler 等）/ Path B / 全量配置生成器；Consequences 含「产物入仓不可手改 + `--adopt` 反灌」模型。`decisions/INDEX.md` 计数 24→25 + ADR-036 行（docs/INDEX.md 不动，按 #277 先例）。
- **8n D-017 anchor 扩展三落点**：ai-agent.md:94 A14 surface cell 增列（派生 `.codex/config.toml`、`.agents/**`、`scripts/sdd/agents_sync.py`、manifest `mcp`/`codex.posture` 段）+ :112-114 措辞同步 + PULL_REQUEST_TEMPLATE.md:67 行同步；governance.contract.yml §a14 声明核对（仅陈述变假处更新）。
- **8o 收口**：全量 Level A + GitHub CI 实跑（新 gate steps 出现且 job 绿）+ #320 AC 勾选证据 + §11.1 P1→P2 晋级证据回填 #320 评论（manifest/checker 单测全绿、required 18 项两侧覆盖、CI `--fail-on error` 无 error）。**state flip 按 #319 先例 post-merge 另开小 PR**（不入本链）。

### Documentation Decision（§7.1 摘要；完整 10 行表见 Stage 3 输出）

Plan=Create（本 2 件，PR-1）；ADR=Create（ADR-036，PR-3）；INDEX=Update（decisions/INDEX.md，PR-3）；SPEC/RUNBOOK/GUIDE/STANDARD/Local ISSUE/ASSESSMENT/CHANGELOG=None。

## 5. 风险（Risk Level: High）

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| manifest 37 条手工著录与仓库现实漂移 | Medium | C | checker required/引用/canary 自动核 + PR-2 review 逐条；rollback = revert |
| 闭包规则口径与 S1 白名单互锁（过严缩空/过松放行） | Medium | C | Handoff 窄定义 + 空态 warning（拍板项 5）；S1 以 checker 输出定白名单 |
| ci.yml 新增 steps 被误判 blocking flip | Low | C | `continue-on-error: true` 显式；PR body 声明非 `ci-blocking-gate-toggle` |
| `@AGENTS.md` import 语义依赖官方行为（嵌套相对解析） | Low | C | Stage 10 本机交互核验；失败回退 = 纯文本指针句，不阻塞其余产物 |
| 嵌套 AGENTS.md 在既有 CI 扫描域外（tests/ 不入 wikilink walk；frontmatter SCAN_ROOTS 不含） | Low | C | 内容无 wikilink + 无 frontmatter（§2.6 扩展注册）；存在性/引用关系由 V8 checker 接管 |
| kernel policies 编辑连带（documentation.md / ai-agent.md / gates.md） | Medium | C | 最小 diff + A4 wikilink 门 + PR review；rollback = revert |
| 退出码/JSON 契约与 §12 S1-S6 fixture（P2）耦合返工 | Low | C | §10 接口逐字实现 + 单测钉住（S5 fixture 命令直接复用本 CLI） |
| manifest `mcp`/`codex.posture` 段初值不当 | Low | C | 三档默认 never + biz/ssh 永 never（D-013）；posture 初值 PR-2 review 再确认（拍板项 7） |

## 6. 验证

### 6.1 Stage 10 Level A（只读 / 必跑，每 PR）

```
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit tests/eval -q
python -m compileall src
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
uv run python scripts/sdd/check_claude_skill_contracts.py --all   # 37/37 PASS
```

- PR-2 附加：`uv run python scripts/sdd/check_development_agent.py --all --fail-on error`（exit 0）· `--json` 输出 schema spot-check · `uv run python scripts/sdd/check_agents_projection.py --all`（空态 exit 0）
- PR-3 附加：GitHub Actions 实跑——新 gate steps 出现、warning 姿态生效、job 整体绿

### 6.2 Level B

无（无运行时行为变更，不需 DB/LLM/compose）。

### 6.3 Stage 11 tie-in

- 反向扫描：AGENTS.md 叙述面 7 文件（documentation.md:145 / archive.md:140 / ai-agent.md §1 / claude-code-skill.md:37 / docs/INDEX.md:23 / README.md:13 / CONTRIBUTING.md:202）——嵌套化后陈述是否变假
- scope-drift 预期：Severity ≤ Minor（文件清单已闭合；新增 = 4 AGENTS.md + 1 yml + 1 adapter md + 2 checker + 1 测试 + 1 ADR + 2 plans）

## 7. 完成标准（AC）

- [ ] 4 嵌套 AGENTS.md + 根 AGENTS.md 增量 + 5 处 CLAUDE.md `@AGENTS.md` 落地；§2.6 扩展 + §4 cadence 注册
- [ ] manifest 符合 §9 契约（37 条目 / 枚举合法 / required 18 项两侧覆盖 / projection 🟢5🟡21🔴11 / mcp 14 servers 三档 / posture 段就位 / 无 owner_agent）
- [ ] `check_development_agent.py` §10 接口逐项可证（互斥/--json/--fail-on/退出码 0/1/2）；真实树 `--all --fail-on error` exit 0
- [ ] `check_agents_projection.py` 空态 exit 0；三规则负例单测非零退出
- [ ] 双发现 canary：on-disk ≟ manifest ≟ SKILL_INDEX = 37
- [ ] ci.yml 2 steps warning 姿态接入 + gates.md V8/V9 注册；GitHub CI 实跑绿
- [ ] ADR-036 accepted + decisions/INDEX.md 25；D-017 anchor 扩展三落点齐
- [ ] 每 PR Level A 全绿；3 PR 依序 merge；#320 关闭；#312 P1/S0 行勾选 + 晋级证据回填
- [ ] post-merge follow-up：两 plans state flip（另开小 PR，#319 先例）

## 8. 关联

- Issue: #320（本切片）/ #312（总锚）
- 目标文件：`AGENTS.md` · `capabilities/AGENTS.md`〔新〕· `docker/AGENTS.md`〔新〕· `src/mj_agent/AGENTS.md`〔新〕· `tests/AGENTS.md`〔新〕· `CLAUDE.md` + 4 嵌套 `CLAUDE.md` · `policies/documentation.md` · `policies/archive.md`（核对）· `sdd/development-agent.yml`〔新〕· `sdd/adapters/development-agent.md`〔新〕· `scripts/sdd/check_development_agent.py`〔新〕· `scripts/sdd/check_agents_projection.py`〔新〕· `tests/unit/test_sdd_development_agent.py`〔新〕· `.claudeignore` · `.github/workflows/ci.yml` · `sdd/gates.md` · `decisions/ADR-036_*.md`〔新〕· `decisions/INDEX.md` · `policies/ai-agent.md` · `.github/PULL_REQUEST_TEMPLATE.md` · `capabilities/infrastructure/mcp-server-governance/contracts/governance.contract.yml`（核对）· plans 2 件〔新〕
- 不动文件：`src/mj_agent/**`（含 4 必停面）· `.claude/**`（含 SKILL_INDEX）· `.mcp.json` · `config/secrets*.enc` / `.env` · `archive/**` · docs/INDEX.md（ADR 注册走 decisions/INDEX.md，#277 先例）
- 后续独立 PR / 议题：S1（agents_sync + 首批投影 + drift gate + AGENTS.md 契约条）；S2（3 spikes + emitter B + MCP gate day-1 blocking）；S3（doctor + blocking 转正）；plans state flip 小 PR；#312 登记 4 项独立拍板议题
