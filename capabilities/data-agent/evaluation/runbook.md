---
type: capability-runbook
capability: data-agent.evaluation
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
last_verified: null
---

# Runbook: Offline EVAL Replay

> 离线核心已实现并通过合成回放；CLI／actual入口延期。Agent负责技术操作与分轮角色核验；完整capability未验收，last_verified=null。

## §1 TL;DR

用显式批准的脱敏观测、dataset、manifest 和静态 reference 离线评判；通过完整性、红线和兼容基线三条结果轴解读报告。详见 [design](design.md)。

## §2 Trigger

在 runner 实现并经独立授权后，使用本 RUNBOOK 回放已经取得且批准使用的观测，或执行标记 synthetic 的 judge 自测。需要新的 runtime 观测时返回 target Issue 的批准采样路线，本 RUNBOOK 不采样、不执行 SQL、不连接服务。

## §3 Pre-checks

- [ ] 核对当前对象与授权；已有离线核心编码、合成验收及文档范围复用Owner授权；CLI／actual采样另行授权。
- [ ] 准备 config、22-case dataset、observations、manifest、reference；必要 reviews 与 baseline 独立提供。
- [ ] 确认输入为普通本地文件，无秘密、raw rows、business_summary 或 PII；脱敏审阅与采样批准来源在 manifest 中具名。
- [ ] 核对 schema、实际装配摘要、原始文件摘要、模型／采样、time_basis 与来源，不以 prompt 版本或 baseline_value 代替。
- [ ] 为输出指定新普通本地目录；不要覆盖输入或已有报告，不自动删除旧目录。
- [ ] actual 的完整轨迹／回复与必要人工审阅齐备；缺证据允许报告缺口，不能强填 complete=true。

## §4 Steps

1. 按设计中的白名单准备归一化输入。保留所有 execute_sql 尝试及错误代码，不把最终成功 SQL 放到首次位置。
2. synthetic 来源由 Agent 模拟业务／Prompt 标签，并在 SWE 核验轮从原始输入独立复核，生成绑定摘要和两轮引用的角色记录；不要求真人参与。actual 来源保留 target 原有的全部语义、5 条红线与至少 3 条非红线审计条件；能力未就绪时延期，不要求 Owner 代做技术整理。缺记录保持 REVIEW_REQUIRED。
3. 当前由Agent调用私有core._replay(_Inputs)，显式提供config／dataset／observations／manifest／reference／reviews／baseline的bytes，返回dict与markdown；核心不读写文件。运行受控测试：uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q。design §2.1的CLI命令继续延期，不可执行。
4. 读取 report.json 和 report.md。核对 planned=22、observed、judged、missing／incomplete／review_required／unsupported 等；这些缺口计数可以重叠。
5. 查看 measurement、safety、regression 与全部 reasons，不能仅凭退出码或某个 PASS 行判断 suite 完成。
6. 对同一bytes输入重复回放并比较规范化返回值；测试验证一致。将返回值保存成文件时由Agent在指定新目录核对目标未存在；这不证明未来CLI已实现防覆盖或路径策略。分类码是返回数据，尚不是CLI进程退出码。

## §5 Verification

| 结果 | 解释／下一步 |
|---|---|
| exit 2 | 输入／IO 无效；按安全 reason_code 修正批准文件，不回显原始载荷 |
| exit 6 | 红线或硬回归；先审阅具体证据和观测完整性，不能用缺基线解释成通过 |
| exit 3 | 未测／待审／不支持或 fixture-only；补已批准输入或审阅，不删 dataset case |
| exit 5 | 基线条件不兼容；分别保留报告，不能强制计算回归 |
| exit 4 | 已测但无有效基线；不声称 regression PASS |
| exit 7 | soft regression／有实际支持的 latency warning；返回 Owner 决策 |
| exit 0 | 完整实际测量、红线 CLEAR、兼容有效基线、无回归；仍按 target Issue 的独立 AC 验收 |

synthetic PASS 只证明 judge／runner 测试，不形成 runtime metric／baseline。runtime metric=null 是明确未测，不替换成 0.0。每个 FAIL case 仍可能 judgment_complete=false。

Agent／CI pytest 只通过 scripts/sdd/run_offline_pytest.py；不因凭据存在启用外部腿。静态文档／schema PASS 不代表运行证据。

## §6 Rollback

停止使用错误报告作验收依据，保留原输入和输出的摘要与安全来源记录。取得批准的修正输入后在新目录离线重放，不修改 runtime 或历史报告，不自动删除文件。若涉及代码或正式契约变更，返回相应审批与验证流程。

## §7 Post-mortem Trigger

发现缺观测却输出 PASS、首次失败被后续成功覆盖、synthetic 被当实际基线、红线失败被无基线掩盖、秘密读取或网络连接时，停止使用该 runner 版本的报告并保留脱敏证据；按 [bugfix-drift workflow](../../../sdd/workflows/bugfix-drift.md) 诊断。不会因此授权 live、runtime 修复或发布外部消息。

关联：[Issue #582](https://github.com/MJ-AgentLab/mj-agent/issues/582)、[Plan](../../../plans/[PLAN]_582_offline_eval_runner.md)、[requirements](requirements.md)、[tasks](tasks.md)。

## 延期记录

- 原因：Owner已授权并验收离线核心测试范围；CLI公开main锚点及文件IO未实现，actual采样继续在当前授权之外。
- 替代验证手段：63项单元与6项BDD在合成输入上通过，包含核心无IO／应用导入／网络哨兵；JSON／Markdown报告为SELFTEST_ONLY。不能替代CLI路径／输出保护、actual来源真实性或runtime EVAL。
- 升级触发条件：后续对CLI文件接口／公开main作具体授权并具备路径、输出和端到端验收条件时，由Agent接入验证；actual入口另按原target采样与审阅条件处理。
- 预计时间：不承诺未经授权的执行日期；具备上述条件后安排，当前延期状态明确保留。未实质变化的文档／契约操作继续复用已有授权。

## 本轮交付证据

[核心验收报告](evidence/reports/2026-10-12_offline_core_acceptance.md)、[合成报告](evidence/reports/2026-10-12_synthetic_replay.md)和[合成JSON](evidence/reports/2026-10-12_synthetic_replay.json)。正式metric=null、baseline_eligible=false。部分单元／BDD使用虚构actual条件验证分支，未生成实际运行报告；Owner不代跑技术步骤。
