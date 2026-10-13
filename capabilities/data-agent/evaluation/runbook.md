---
type: capability-runbook
capability: data-agent.evaluation
state: draft
version: "0.8"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-13
last_verified: null
---

# Runbook: Offline EVAL Replay

> 当前T-007c Windows fixed NTFS synthetic-only来源检查CLI已随#599集成；既有T-007a/b已随#595集成。原轮次记录保留历史；完整capability未接受，actual/runtime/来源与target接受及Linux/macOS原生保护继续延期，idea/last_verified=null。当前集成证据见[合并后核验](evidence/reports/2026-10-13_source_inspection_cli_post_merge.md)。

## §1 TL;DR

用显式批准的脱敏观测、dataset、manifest 和静态 reference 离线评判；通过完整性、红线和兼容基线三条结果轴解读报告。详见 [design](design.md)。

## §2 Trigger

在已有任务授权范围内，回放已经取得且批准使用的观测，或执行标记synthetic的judge／runner自测。需要新runtime观测时返回target Issue批准采样路线；本RUNBOOK不采样、不执行SQL、不连接服务。

## §3 Pre-checks

- [ ] 核对对象、输入、环境及任务授权；当前synthetic-only CLI实现／离线测试复用本线程集中授权（Plan §8.7／§8.9），actual文件入口及采样另行授权。
- [ ] 准备 config、22-case dataset、observations、manifest、reference；必要reviews独立提供；可选--baseline只读取明确指定的本地候选JSON object；不提供时为b''。
- [ ] 确认输入为普通本地文件，无秘密、raw rows、business_summary 或 PII；脱敏审阅与采样批准来源在 manifest 中具名。
- [ ] 核对 schema、实际装配摘要、原始文件摘要、模型／采样、time_basis 与来源，不以 prompt 版本或 baseline_value 代替。
- [ ] 为输出指定repo_root内的新普通本地目录，父目录必须已存在；已有空目录也拒绝。不覆盖或删除输入／旧报告。repo_root缺省cwd，调用API时注入绝对Path；不扫描Git、不展开变量/~或..。
- [ ] manifest必须声明synthetic_fixture；使用显式--synthetic-fixture。runtime_observation只读manifest后返回2/ACTUAL_ENTRY_DEFERRED，不进入其他载荷读取、replay或输出创建。

## §4 Steps

1. 按设计中的白名单准备归一化输入。保留所有 execute_sql 尝试及错误代码，不把最终成功 SQL 放到首次位置。
2. synthetic 来源由 Agent 模拟业务／Prompt 标签，并在 SWE 核验轮从原始输入独立复核，生成绑定摘要和两轮引用的角色记录；不要求真人参与。actual 来源保留 target 原有的全部语义、5 条红线与至少 3 条非红线审计条件；能力未就绪时延期，不要求 Owner 代做技术整理。缺记录保持 REVIEW_REQUIRED。
3. 使用下方CLI命令传入文件，reviews按需要提供；可选baseline按下述规则提供，synthetic不启动实际比较。文件适配层调用公开core.replay(schema.ReplayInputs)，纯内存核心仍无文件IO。若只使用核心API，直接提供七项bytes即可。
4. 读取 report.json 和 report.md。核对 planned=22、observed、judged、missing／incomplete／review_required／unsupported 等；这些缺口计数可以重叠。
5. 查看 measurement、safety、regression 与全部 reasons，不能仅凭退出码或某个 PASS 行判断 suite 完成。
6. 相同输入在两个新目录回放，JSON／Markdown字节与实际进程退出码保持一致。CLI安全诊断不回显路径／载荷；读写失败为2，可能留下部分报告。核实已发生副作用，保留部分输出并换新目录重试，不重复覆盖。

    uv run --frozen --no-sync python -m mj_agent.evaluation.runner --synthetic-fixture --eval-config <config.json> --dataset <dataset.jsonl> --observations <observations.jsonl> --manifest <manifest.json> --reference <reference.json> --output-dir <new-local-directory> [--reviews <reviews.jsonl>] [--baseline <baseline.json>]

仓内固定自测可将前五项依次指向tests/unit/fixtures/eval_core/中的同名文件，eval-config对应config.json，并加--reviews tests/unit/fixtures/eval_core/reviews.jsonl。预期退出3，planned=judged=22、SELFTEST_ONLY、metrics=null、baseline_eligible=false；这是预期自测状态，不能改为退出0宣称runtime通过。

    uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q

baseline示例仅作合成文件接入自测：增加--baseline tests/unit/fixtures/eval_cli/baseline.synthetic.json。该文件为历史SELFTEST_ONLY报告的固定原bytes，不是有效runtime基线；提供或省略它的报告字节相同、退出3、regression=NOT_EVALUATED。省略baseline与显式空文件不同；空文件返回BASELINE_INPUT_EMPTY，null／数组／标量返回BASELINE_NOT_OBJECT，非法UTF-8／JSON返回INVALID_INPUT_SCHEMA。其他解析限制和10MiB上限保持。非法baseline不调用核心或创建输出。

manifest仍先读；actual标签不会触发baseline或观测读取。报告内路径／引用不自动访问。验收记录单独保存baseline/reviews原文件摘要，不把manifest现有四项hash误称为完整七输入绑定。

### 4.1 T-007b纯内存来源检查

Agent先取得当前范围批准使用的显式bytes，在调用方自行完成输入传递；本接口没有CLI参数和文件IO。仅使用已在内存的inputs：

```python
from mj_agent.evaluation.inspection import inspect_source

inspection = inspect_source(inputs)  # inputs是既有ReplayInputs；不自动读取文件或引用
```

INVALID/exit_code=2仅表示结构或身份错误；VALID/3表示仅检查。CONSISTENT表示提供记录结构齐全且已有review关联匹配；无review也可能CONSISTENT，覆盖始终NOT_CHECKED。INCOMPLETE时按gaps核对缺观测、complete标志、unknown结果、SQL为null及提供review绑定；不从缺记录推导业务失败或PASS。

source/target始终UNVERIFIED；引用、方法标签、body/assembled hash没有真实性检查，不能凭此提升授权或验收状态。runtime_metrics=null、baseline_eligible=false；此字典不是offline-report-v1，不能充当runtime baseline。exit_code为返回数据，不是新增进程入口。相同输入输出确定性一致，API本身不保存报告。

### 4.2 后续真实观测包依赖（本轮不采样）

当前无获批脱敏观测包。Agent负责后续文件核验与技术整理；Owner只补必要来源/采样及脱敏审阅引用，并作实质授权/最终接受。材料必须绑定采样环境、run、批准范围和脱敏版本；保留22条完整case、调用ID/顺序/参数/结果及首次SQL/所有失败，不含业务行数据。

目标证据应来自真实_ACTIVE_SKILLS顺序及load_prompt/load_skill去frontmatter后的body、provider/model Runtime段和最终拼接hash；静态文件hash或synthetic的单skill不能证明实际装配。旧walkthrough脚本仅5场景/截断markdown，无完整调用结果关系，也在加载时读取dotenv，不用于本轮导入/执行或冒充完整包。

actual语义审阅仍需全部必要项、5条红线和至少10%（当前3条非红线）抽检，并使用绑定真实观测的independent_review；不将synthetic角色记录重命名为actual证据。same_target_replay的commit/target/model/采样/时间/来源兼容与0.03阈值保持；#161跨版本A/B另议具体比较契约，其他target原scope不改。

实际入口待材料就绪、单独方案与授权；Linux/macOS须有等价原生祖先rename等保护证明，否则继续fail closed。内存API的跨平台模型测试与Linux类型检查不替代原生文件运行。

### 4.3 T-007c Windows synthetic-only来源检查文件入口

    uv run --frozen --no-sync python -m mj_agent.evaluation.inspection_runner --synthetic-fixture --eval-config <config.json> --dataset <dataset.jsonl> --observations <observations.jsonl> --manifest <manifest.json> --reference <reference.json> --output-dir <new-directory> [--reviews <reviews.jsonl>] [--baseline <baseline.json>]

固定本地自测：五必填依次指向tests/unit/fixtures/eval_core/中的config.json、dataset.jsonl、observations.jsonl、manifest.json、reference.json，reviews指向同目录reviews.jsonl；baseline可省略或使用tests/unit/fixtures/eval_cli/baseline.synthetic.json。输出父目录必须已存在且目录名未使用。程序只写inspection.json，预期3、22/22完整观测、34/34提供绑定、UNVERIFIED/NOT_CHECKED/null/false。没有review也可CONSISTENT；不据此宣称必要审阅齐全。

help0不读文件；缺模式/非法参数2。manifest先读，actual2/ACTUAL_ENTRY_DEFERRED早拒绝，其他输入和baseline不读；路径词法安全检查可更早拒绝。baseline空/非object分别BASELINE_INPUT_EMPTY/BASELINE_NOT_OBJECT；其他错误沿用安全解析码。任何结构INVALID（含API返回2）均不创建输出，只发stderr诊断。VALID的INCOMPLETE同样写inspection.json并退出3，按gaps整理结构缺口；不执行EVAL或判FAIL/PASS。

write/close故障2，可能已经有新目录/inspection.json；按安全inspection_exit_code核对实际副作用，保留部分输出，新目录重试，不自动覆盖或删除。不承诺原子/耐久性。Linux/macOS无等价祖先rename保护继续FS_CAPABILITY_UNAVAILABLE；跨平台类型或内存模型不计原生入口通过。

### 4.4 真实观测包最小材料清单（准备用途；当前无获批包）

- 采样环境非秘密标识、run/commit、模型部署/有效参数、时间基准、采样批准、来源、脱敏版本与审阅引用绑定。
- 22case完整初始turn、连续sequence与唯一call_id、全部工具调用及outcome、首次SQL和所有失败；零调用须完整轨迹。必要完整脱敏回复支持语义审阅。
- 禁业务行数据、business_summary、PII、凭据、完整tool返回envelope；自由文本/SQL/错误需真实脱敏审阅，不以有限scanner证明。
- 实际loader返回body、算法/编码、采样commit的_ACTIVE_SKILLS顺序、有效Runtime段、最终拼接正文与摘要；静态文件hash不证明实际缓存/装配。
- 全部必要语义项、5红线及按case ID排序至少3条非红线审计，independent_review材料绑定run/obs规范摘要/config/reference原bytes/judge规则；方法标签不证明独立性。Agent负责技术整理与独立审阅，Owner负责实质决定及最终接受。
- 现有_Call不含其他工具参数摘要，manifest也无独立环境/loader正文容器。上述附属材料在单独脱敏材料侧绑定，不塞未知字段、不扩schema；T-007c不读取其引用。
- 软件可核字段、摘要、顺序、关联和装配重算；不能单凭字段/hash证明采样发生、没有隐去轨迹、无敏感文本、真实独立审阅或Owner授权有效。
- 保留same_target_replay同commit/target/model/采样/时间/来源条件、完整分母、0.03与红线；#161跨版本A/B及其他target原scope另议。缺材料/能力仅延期对应actual/平台入口，不造PASS。

当前合并版本891fd5e、复现及新raw binding见[合并后核验](evidence/reports/2026-10-13_source_inspection_cli_post_merge.md)；[CLI验收](evidence/reports/2026-10-13_source_inspection_cli_acceptance.md)保留原交付/接受时点。材料契约与后续门禁的[提案](evidence/reports/2026-10-13_t007_actual_material_proposal.md)尚待Owner决定范围，当前命令仍synthetic-only。#582 OPEN、Plan active、idea/last_verified=null保持。

## §5 Verification

| 结果 | 解释／下一步 |
|---|---|
| exit 2 | 输入／IO 无效；按安全 reason_code 修正批准文件，不回显原始载荷 |
| exit 6 | 红线或硬回归；先审阅具体证据和观测完整性，不能用缺基线解释成通过 |
| exit 3 | 未测／待审／不支持或 fixture-only；补已批准输入或审阅，不删 dataset case |
| 核心分类5 | 基线条件不兼容；当前CLI actual入口延期，synthetic不比较基线，不可达 |
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

- 原因：离线软件已实现，actual文件入口、实际基线比较、采样／来源真实性及runtime接受延期，仍缺对应方案、能力和单独授权。
- 替代验证手段：264项unit与14项BDD覆盖核心、CLI、baseline文件接入及纯内存来源检查；虚构actual条件仅验证报告分支，不证明来源或真实运行。
- 升级触发条件：target原批准采样与完整审阅条件具备后，取得实际观测，使用相同严格窗口与兼容规则回放。
- 预计时间：不承诺未授权采样日期；actual延期不计作软件测试通过或runtime接受。

## 历史T-007a/b交付证据（当前见§4.3及T-007c验收）

[核心验收报告](evidence/reports/2026-10-12_offline_core_acceptance.md)、[合成报告](evidence/reports/2026-10-12_synthetic_replay.md)和[合成JSON](evidence/reports/2026-10-12_synthetic_replay.json)。正式metric=null、baseline_eligible=false。部分单元／BDD使用虚构actual条件验证分支，未生成实际运行报告；Owner不代跑技术步骤。

当前T-007a复现、角色核验和版本绑定见[baseline CLI验收](evidence/reports/2026-10-12_baseline_cli_acceptance.md)。T-006已随#589合并，原[CLI验收](evidence/reports/2026-10-12_synthetic_cli_acceptance.md)和其他旧报告保留历史结果；本轮T-007a已完成同Agent分轮核验，供Owner最终接受，未提交或发布。Windows固定NTFS入口已验证；Linux原生入口DEFERRED_FS_CAPABILITY/NOT_RUN，其他平台/文件系统若保护能力不足则返回2/FS_CAPABILITY_UNAVAILABLE，不回退普通open。两份报告不是原子提交；成功也不声称fsync耐久性。

T-007b最新软件和绑定证据见[来源检查验收](evidence/reports/2026-10-12_source_inspection_acceptance.md)与[BDD](evidence/bdd/2026-10-12_source_inspection_scenarios_pass.md)。原T-007a报告/绑定保留历史；回到本地38文件快照核对当轮原bytes，不将历史fingerprint冒称当前工作树指纹。
