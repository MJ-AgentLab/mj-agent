---
type: capability-runbook
capability: data-agent.evaluation
state: draft
version: "0.5"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
last_verified: null
---

# Runbook: Offline EVAL Replay

> 离线核心与CLI已通过软件自测。Agent负责技术操作与核验；actual采样、来源真实性及runtime接受仍延期，完整capability未接受、last_verified=null。

## §1 TL;DR

用显式批准的脱敏观测、dataset、manifest 和静态 reference 离线评判；通过完整性、红线和兼容基线三条结果轴解读报告。详见 [design](design.md)。

## §2 Trigger

在已有任务授权范围内，回放已经取得且批准使用的观测，或执行标记synthetic的judge／runner自测。需要新runtime观测时返回target Issue批准采样路线；本RUNBOOK不采样、不执行SQL、不连接服务。

## §3 Pre-checks

- [ ] 核对对象、输入、环境及任务授权；当前synthetic-only CLI实现／离线测试复用本线程集中授权（Plan §8.7），actual文件入口及采样另行授权。
- [ ] 准备 config、22-case dataset、observations、manifest、reference；必要reviews独立提供；CLI不接受baseline文件参数。
- [ ] 确认输入为普通本地文件，无秘密、raw rows、business_summary 或 PII；脱敏审阅与采样批准来源在 manifest 中具名。
- [ ] 核对 schema、实际装配摘要、原始文件摘要、模型／采样、time_basis 与来源，不以 prompt 版本或 baseline_value 代替。
- [ ] 为输出指定repo_root内的新普通本地目录，父目录必须已存在；已有空目录也拒绝。不覆盖或删除输入／旧报告。repo_root缺省cwd，调用API时注入绝对Path；不扫描Git、不展开变量/~或..。
- [ ] manifest必须声明synthetic_fixture；使用显式--synthetic-fixture。runtime_observation只读manifest后返回2/ACTUAL_ENTRY_DEFERRED，不进入其他载荷读取、replay或输出创建。

## §4 Steps

1. 按设计中的白名单准备归一化输入。保留所有 execute_sql 尝试及错误代码，不把最终成功 SQL 放到首次位置。
2. synthetic 来源由 Agent 模拟业务／Prompt 标签，并在 SWE 核验轮从原始输入独立复核，生成绑定摘要和两轮引用的角色记录；不要求真人参与。actual 来源保留 target 原有的全部语义、5 条红线与至少 3 条非红线审计条件；能力未就绪时延期，不要求 Owner 代做技术整理。缺记录保持 REVIEW_REQUIRED。
3. 使用下方CLI命令传入文件，reviews按需要提供；baseline CLI参数延期。文件适配层调用公开core.replay(schema.ReplayInputs)，纯内存核心仍无文件IO。若只使用核心API，直接提供七项bytes即可。
4. 读取 report.json 和 report.md。核对 planned=22、observed、judged、missing／incomplete／review_required／unsupported 等；这些缺口计数可以重叠。
5. 查看 measurement、safety、regression 与全部 reasons，不能仅凭退出码或某个 PASS 行判断 suite 完成。
6. 相同输入在两个新目录回放，JSON／Markdown字节与实际进程退出码保持一致。CLI安全诊断不回显路径／载荷；读写失败为2，可能留下部分报告。核实已发生副作用，保留部分输出并换新目录重试，不重复覆盖。

    uv run --frozen --no-sync python -m mj_agent.evaluation.runner --synthetic-fixture --eval-config <config.json> --dataset <dataset.jsonl> --observations <observations.jsonl> --manifest <manifest.json> --reference <reference.json> --output-dir <new-local-directory> [--reviews <reviews.jsonl>]

仓内固定自测可将前五项依次指向tests/unit/fixtures/eval_core/中的同名文件，eval-config对应config.json，并加--reviews tests/unit/fixtures/eval_core/reviews.jsonl。预期退出3，planned=judged=22、SELFTEST_ONLY、metrics=null、baseline_eligible=false；这是预期自测状态，不能改为退出0宣称runtime通过。

    uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q

## §5 Verification

| 结果 | 解释／下一步 |
|---|---|
| exit 2 | 输入／IO 无效；按安全 reason_code 修正批准文件，不回显原始载荷 |
| exit 6 | 红线或硬回归；先审阅具体证据和观测完整性，不能用缺基线解释成通过 |
| exit 3 | 未测／待审／不支持或 fixture-only；补已批准输入或审阅，不删 dataset case |
| 核心分类5 | 基线条件不兼容；当前CLI的actual/baseline入口延期，不可达 |
| 核心分类4 | 已测但无有效基线；当前CLI不可达 |
| 核心分类7 | soft regression；当前CLI不可达 |
| CLI help0／核心分类0 | help0不读取文件、不表示EVAL通过；核心actual完整无回归分类0在当前CLI不可达 |

synthetic PASS 只证明 judge／runner 测试，不形成 runtime metric／baseline。runtime metric=null 是明确未测，不替换成 0.0。每个 FAIL case 仍可能 judgment_complete=false。

Agent／CI pytest 只通过 scripts/sdd/run_offline_pytest.py；不因凭据存在启用外部腿。静态文档／schema PASS 不代表运行证据。

## §6 Rollback

停止使用错误报告作验收依据，保留原输入和输出的摘要与安全来源记录。取得批准的修正输入后在新目录离线重放，不修改 runtime 或历史报告，不自动删除文件。若涉及代码或正式契约变更，返回相应审批与验证流程。

## §7 Post-mortem Trigger

发现缺观测却输出 PASS、首次失败被后续成功覆盖、synthetic 被当实际基线、红线失败被无基线掩盖、秘密读取或网络连接时，停止使用该 runner 版本的报告并保留脱敏证据；按 [bugfix-drift workflow](../../../sdd/workflows/bugfix-drift.md) 诊断。不会因此授权 live、runtime 修复或发布外部消息。

关联：[Issue #582](https://github.com/MJ-AgentLab/mj-agent/issues/582)、[Plan](../../../plans/[PLAN]_582_offline_eval_runner.md)、[requirements](requirements.md)、[tasks](tasks.md)。

## 延期记录

- 原因：离线软件已实现，actual文件入口、baseline CLI参数、采样／来源真实性及runtime接受延期，仍缺对应方案、能力和单独授权。
- 替代验证手段：169项unit与10项BDD覆盖核心及CLI；虚构actual条件仅验证报告分支，不证明来源或真实运行。
- 升级触发条件：target原批准采样与完整审阅条件具备后，取得实际观测，使用相同严格窗口与兼容规则回放。
- 预计时间：不承诺未授权采样日期；actual延期不计作软件测试通过或runtime接受。

## 本轮交付证据

[核心验收报告](evidence/reports/2026-10-12_offline_core_acceptance.md)、[合成报告](evidence/reports/2026-10-12_synthetic_replay.md)和[合成JSON](evidence/reports/2026-10-12_synthetic_replay.json)。正式metric=null、baseline_eligible=false。部分单元／BDD使用虚构actual条件验证分支，未生成实际运行报告；Owner不代跑技术步骤。

当前候选CLI及复现、版本绑定见[CLI软件验收记录](evidence/reports/2026-10-12_synthetic_cli_acceptance.md)；旧报告仅保存历史结果。本线程已完成同Agent分轮核验，Owner最终接受与发布授权尚未记录。Windows固定NTFS入口已验证；Linux原生入口DEFERRED_FS_CAPABILITY/NOT_RUN，其他平台/文件系统若保护能力不足则返回2/FS_CAPABILITY_UNAVAILABLE，不回退普通open。两份报告不是原子提交；成功也不声称fsync耐久性。
