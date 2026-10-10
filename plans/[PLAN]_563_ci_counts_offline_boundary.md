---
type: plan
summary: Issue 563 六处 CI 名称去除历史计数与阶段说明，补齐离线测试执行边界文档
owner: ranzuozhou
created: 2026-10-10
updated: 2026-10-10
completed: 2026-10-10
state: completed
track: engineering-workflow
---

# Issue #563 CI 计数说明与离线测试执行边界

## 追踪与批准

- Issue：[GitHub #563](https://github.com/MJ-AgentLab/mj-agent/issues/563)。
- 基线：`develop@3c3c52b49bd2a4e215791d14d8f5935ca1abc22c`；分支 `maintain/563-ci-counts-offline-boundary`，通过 `git worktree add` 从 develop 创建独立工作树。
- Owner 在当前会话明确批准实施完整计划，包括六处 CI 名称、`sdd/gates.md` 末尾 §6、版本与更新日期、修订记录，以及本 working Plan。
- Owner 选择精简名称：只保留检查用途和当前门禁姿态；G21 保留风险子集说明。历史阶段来源与基线计数继续保留在 Issue 记录及既有历史正文中。
- 实施与约定的本地验证完成后，Owner 于 2026-10-10 明确授权提交本次三份修改、按 Gitee → GitHub 顺序普通双推，并创建目标为 develop 的 PR。各项实际执行结果以提交、远端引用和 PR 记录为准；merge 与验收由 Owner 执行。Issue 保持 OPEN，本 Plan 保持 active。

## 范围与实施顺序

1. 核对独立工作树身份与干净状态，不处理 develop 中其他任务的未提交内容。
2. 仅替换 `.github/workflows/ci.yml` 的六个名称；解析前后 YAML 确认其他字段完全一致。
3. 在 `sdd/gates.md` 末尾追加 §6 测试执行边界；版本 `"0.16"` → `"0.17"`、updated → `2026-10-10`，追加 #563 修订记录。既有正文及 state 保留。
4. 运行约定检查与既有离线边界单元测试，逐项记录真实输出、退出码、AC 和未测项。

| 检查器 | 批准的新名称 |
|---|---|
| G1 | `G1 capability schema (BLOCKING)` |
| G2 | `G2 traceability (BLOCKING)` |
| G8 | `G8 capability evidence required (BLOCKING)` |
| G19 | `G19 BDD scenario trace (BLOCKING)` |
| G21 | `G21 BDD acceptance (BLOCKING; @risk:critical\|high subset)` |
| G3 | `G3 contracts (WARNING)` |

命令、条件、continue-on-error、workflow 触发条件、Tests/BDD/Contract 精确名称与调用均保持原样。无公共 API、类型、依赖或运行时行为变化；不改执行脚本、测试代码、原生配置、契约、Docker 或运行时资产。

## 文档决策

| 类型 | 决策 |
|---|---|
| Plan | 新建本 working Plan，记录批准范围、验证与 AC |
| SPEC | 无接口或行为契约变化，无需修改 |
| ADR | 无新架构决策，无需修改 |
| RUNBOOK | 无操作流程变化，无需修改 |
| GUIDE | 无需修改 |
| STANDARD／SDD 内核 | 更新既有 `sdd/gates.md`，保持 shared track 与 active state |
| Local ISSUE | 使用 GitHub #563，无需新增 |
| ASSESSMENT | 证据记入本 Plan，无需新增 |
| CHANGELOG | 无用户可见行为变化，无需修改 |
| INDEX | 无 canonical 路径或入口变化，无需修改 |

## 风险与恢复

风险维持 Medium，风味 C infra／工程流程说明修复。六个名称只承载展示信息；Tests/BDD/Contract 另有精确名称与命令校验，保留原值。追加 §6 保留旧章节位置，元数据变更不改变审批和门禁姿态。受保护 CI／SDD 具体差异已有 Owner 批准；若正常工具发生技术拒绝，保留原错并返回 BLOCKED_EXECUTION_ROUTE，不绕过保护。

恢复来源为上述基线中两份原文件；如需回退，只撤销本次六处名称、两项元数据和追加内容，不覆盖后来变化或其他任务内容。测试复用 develop 既有 Python 环境，无依赖安装或同步。

## 本地验证

执行日期：2026-10-10。所有 Python 命令复用 develop 的 `.venv/Scripts/python.exe`，采用 `-X utf8 -B`；pytest 仅经现有 `scripts/sdd/run_offline_pytest.py` 执行。未安装或同步依赖，未修改测试代码。

| 检查 | 参数／条件 | 结果 |
|---|---|---|
| CI 与文档差异语义核对 | 对照 Git 基线；六个 name 之外 YAML 相等；旧文档正文完整保留；仅批准的元数据和追加内容 | exit 0 / PASS；恰六个 name（12 行增删），其余 YAML 相等；旧正文前缀完整保留，仅追加修订记录及 §6；文件范围为批准三份 |
| G1 | `check_capability_schema.py --all` | exit 0 / 6P、0W、0F |
| G2 | `check_traceability.py --all` | exit 0 / 6P、0W、0F |
| G8 | `check_capability_evidence_required.py --all` | exit 0 / 5P、0W、0F、1SKIP |
| G19 | `check_bdd_scenario_trace.py --all --scope full` | exit 0 / 24P、0W、0F |
| G21 | `check_bdd_acceptance.py --all --strict` | exit 0 / 16P、0W、0F；本次采用 runbook justification fallback |
| G3 | `check_contracts.py --all` | exit 0 / 6P、0W、0F |
| offline boundary checker | `scripts/sdd/check_test_offline_boundary.py` | exit 0 / OFFLINE_BOUNDARY: GREEN (static/AST boundary closed) |
| 既有离线边界单元测试 | `scripts/sdd/run_offline_pytest.py tests/unit/test_offline_execution_boundary.py -q` | exit 0 / 74 passed in 8.16s；无 SKIP、deselected |
| 文档元数据 | `scripts/check_frontmatter.py` | exit 0 / 149 canonical docs 合法 |
| 严格链接 | `scripts/check_wikilinks.py`，`MJ_AGENT_A4_STRICT=1` | exit 0 / 13 个 archived files 的 archive-ref 0 violations；5 个 root files 的 unresolved targets 为 0 |
| 原生消费者 | `scripts/sdd/check_native_governance.py --surface consumers` | exit 0 / STATIC_PASS，errors 空；host NOT_TESTED |
| 推送前 lint | 既有 Python 环境执行 `-m ruff check` | exit 0 / All checks passed |
| 推送前类型检查 | 既有 Python 环境执行 `-m mypy src/mj_agent` | exit 0 / 48 source files 无问题 |
| 差异空白与文件范围 | `git diff --check`；变更与未跟踪内容合计仅批准三份文件 | exit 0 / 范围内两份已跟踪修改与本 Plan；无额外未跟踪文件 |

门禁检查器输出属于静态验证。G8 的 1SKIP 对应仍处于 drafting 的 mcp-server-governance capability；本次 74 项 pytest 回归未出现 policy SKIP 或 deselected。不把 G19 结构 PASS 或 G21 runbook fallback 解释为 BDD／真实环境通过。

## AC 与交付状态

| AC | 完成标准 | 状态 |
|---|---|---|
| AC-1 | 六个名称与批准表一致；其他 CI 字段完全相等；步骤名消费者反扫和边界验证通过 | 本地 PASS；自动 YAML／逐行比较、反扫、边界检查与 74 项回归见上表 |
| AC-2 | §6 据真实 runner／checker 调用登记；无新 gate 或姿态变化；旧文档正文保留 | 本地 PASS；§6、仅六处 name 的 YAML 比较及旧正文保留断言 |
| AC-3 | 修改后检查记录齐全；文档／引用／空白通过；未测项及计数类别明确 | 本地 PASS；上表为本次修改后执行结果，静态计数与实际测试分别记录 |

交付为修复差异、本 Plan 与 AC 证据。提交、Gitee → GitHub 双推及 develop PR 创建已获后续明确授权，执行结果在对应 Git／PR 记录及任务回复中记录；合并和最终验收未执行。

## AI 自检与未验证项

实施来源：Codex。HITL：本次具体 CI／SDD 编辑和 Plan 落盘已获 Owner 批准；无 ci-blocking-gate-toggle。BDD/TDD impact NONE：名称和说明修复，不新增测试代码，复用既有边界回归。Subagent dispatched NONE。

范围审阅：三份文件均逐项对应批准计划，scope drift = None。六个步骤名称的消费者反扫仅命中展示行、既有历史注释及检查器／测试说明，未发现依赖六个完整旧名称的执行消费者；Tests/BDD/Contract 的精确绑定原样保留。§6 已对照 runner 的前置检查、受控子进程和退出码流程；旧文档及历史记录保留。

5a 无符号／路径／SQL 对象迁移、运行时 canonical 或 catalog 改动，步骤名称反扫已完成；5b 本 working Plan 已创建；5c 无 INDEX／AGENTS／CHANGELOG 同步变化；5d 不涉及 SPEC Delta。没有敏感信息、秘密读取或调试代码新增。后续 Git／PR 动作复用上述具体授权；无 merge 授权。

本次本地验证未运行完整 pytest、远端 CI、live probe、业务连接、容器生命周期或部署。PR 触发的远端 CI 结果以 GitHub 实际状态为准；静态绿色与本地离线测试不能替代真实环境验收。
