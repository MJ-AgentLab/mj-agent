---
type: capability-tasks
capability: data-agent.evaluation
state: draft
version: "0.5"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
---

# Tasks: Offline EVAL Replay

> Owner已集中授权独立离线核心编码、必要测试、Agent合成验收和回归报告。
> 核心及CLI已完成软件验证，actual采样／runtime验收延期；不修改既有runtime、不执行live或Git发布。当前执行见T-006，原核心任务保留历史轮次结果。

## Done — #587历史核心范围

### T-001 输入校验与完整计划分母（Plan 8a）

- Phase：#582 v1 core；Priority：high；Linked REQ：REQ-001、REQ-005。
- HITL：复用明确的离线核心编码授权，无新保护面。
- TDD：初始RED为模块缺失；已支持检查类型错误在缺观测条件下也必须INPUT_INVALID的反例先RED，再修复。
- GREEN：版本、重复key／ID、外来ID、hash、资源限额、全缺／单缺观测、22条计划结果均有固定断言。
- BDD：Dataset identity and every planned case are preserved，核心执行PASS。
- 文件IO与CLI入口不在本任务Done范围。

### T-002 首次SQL、AST与完整轨迹（Plan 8b）

- Phase：#582 v1 core；Priority：critical；Linked REQ：REQ-002、REQ-003。
- HITL：纯离线新增模块，不改precheck／guardrail。
- TDD：日期溢出、单次被拒误判回环反例先RED，再修复；首轮失败后成功、投影日期、OR TRUE、维表过滤、daily／monthly配对、COUNT(*)与t.*、DDL／多语句、未知scope均有固定预期。
- GREEN：全部尝试保留，安全否定独立检查，未知语义不强填PASS。
- BDD：A repaired final SQL does not hide the first failed attempt，核心执行PASS。

### T-003 绑定角色与语义评判（Plan 8c）

- Phase：#582 v1 core；Priority：high；Linked REQ：REQ-002、REQ-005。
- Agent模拟Domain／Prompt标签，独立SWE轮从原始SQL／轨迹／回复／规则复核；同Agent分轮，无真人前置。
- 22条固定合成case、34条绑定review；八条窗口／signal回复描述已校正并重绑摘要，expected.json标签未由实现生成。
- GREEN：缺／过期／冲突review、关键词回复、绑定负面verdict、可选分支与mandatory审计按批准语义判定。
- BDD：Semantic checks require a bound role-review verdict，核心执行PASS。
- actual审阅来源真实性未验证，继续延期。

### T-004 完整性、精确指标与回归（Plan 8d）

- Phase：#582 v1 core；Priority：critical；Linked REQ：REQ-004、REQ-005。
- TDD：基线完整性、case状态、必要check、计数与binding矛盾先RED，再收紧校验。
- GREEN：synthetic隔离、缺证据保留、完整零值、placeholder、兼容键差异、同条件不同run_id、无基线红线、21/22下降、精确0.03及两侧边界、重复回放均验证。
- BDD：A confirmed red-line failure remains hard without a baseline；Synthetic success cannot become a runtime baseline，核心条件执行PASS。
- actual分支只用具名虚构单元条件，未保存成actual报告或基线；退出分类为返回数据，不声称CLI进程退出已验收。

### T-005 离线边界与交付记录（Plan 8e）

- Phase：#582 v1 core；Priority：critical；Linked REQ：REQ-006。
- GREEN：核心不读文件、不导入应用config／dotenv／数据库／LLM客户端、不连接网络；哨兵与确定性检查通过。
- BDD：Replay cannot load application credentials or connect to services，核心执行PASS。
- pytest_plugins绑定曾被既有受控边界检查拒绝；已改成既有tests/bdd/<domain>/<capability>单模块步骤布局，未修改守卫或执行器。
- 本轮64项单元＋6项BDD经公开API通过，ruff与全src mypy通过；trace、索引、Plan、RUNBOOK、CHANGELOG及报告同步。
- 完整capability未验收，保持idea／last_verified=null；正式Python契约已绑定ReplayInputs／replay，V1默认模式无FAIL；CLI main仅保留为延期候选。

## Verified — 本轮 synthetic-only CLI 软件

### T-006 CLI本地文件接口与实际退出

- Priority：high；Linked REQ：REQ-001、REQ-004、REQ-005、REQ-006。
- 状态：VERIFIED_OFFLINE_SOFTWARE；Owner最终接受和发布尚未记录，完整capability未接受。
- 授权：本线程集中批准synthetic-only CLI与契约/文档/必要测试，另批准协调接续；Plan §8.7。原Agent-first委派候选为历史，22文件备份保留。
- T-006a 来源与文件拒绝：main(argv, *, repo_root)；必需synthetic开关；manifest优先；actual早拒绝；有界本地IO、root/软硬链接/reparse/设备/网络/别名/替换保护。
- T-006b 报告与退出：新目录且父已存在，独占报告写入；3=SELFTEST_ONLY、6=合成红线失败、2=参数/来源/IO，help0；actual的0/4/5/7不可达。报告对非原子提交，故障保留部分目录。
- T-006c 固定角色与回归：复用既有22-case/34-role-review固定输入与期望，Codex模拟Domain/Prompt后从原SQL/轨迹/回复作独立SWE轮；未派子Agent。原64项core加105项CLI unit及10项BDD（原6+新4）通过。
- T-006d 契约与文档：真实main签名后扩展python.contract.yml，并对齐已交接cli.contract.yml；同步SPEC/RUNBOOK/trace/索引/CHANGELOG/fixture与证据。
- RED：旧main缺repo_root、缺开关仍读取输入（2 FAIL）；正向Windows输出曾因GENERIC_WRITE不含READ_ATTRIBUTES失败，定位后补最小属性读取权限。synthetic红线固定预期校正为既有SELFTEST_HARD_FAIL，无judge改动。
- 平台：Windows固定NTFS原生正/负向已运行；Linux原生入口DEFERRED_FS_CAPABILITY/NOT_RUN，缺能力入口延期。32类规则、窗口、兼容/阈值、核心API未改；三处报告延期文案及core docstring更正改变报告字节，不重写历史报告。
- 证据：[synthetic CLI验收](evidence/reports/2026-10-12_synthetic_cli_acceptance.md)、[BDD](evidence/bdd/2026-10-12_synthetic_cli_scenarios_pass.md)。
- OFFLINE/RECALL及流构造泄漏反例实测RED后修复，拒绝哨兵验证调用次数而非只看退出2。
- 仅指定测试与固定CLI期望为硬化runner精确暂存；未commit/push/PR/Issue发布、runtime/CI/守卫改动或actual/live执行。

## Backlog — 延期范围

### T-007 actual文件入口、baseline CLI参数及runtime接受

- actual/runtime_observation文件入口、baseline参数、真实采样、来源/脱敏真实性、target审阅与runtime EVAL继续延期。
- 需具体入口方案、可用技术能力及对应授权；Agent承担技术操作，Owner只补必要信息、作实质决定与授权，严格窗口/阈值/接受条件不降低。
- Linux原生文件入口未实际验证；无保护能力时fail closed，不以Windows或模型测试替代。
- RED/GREEN：NOT_RUN，不计T-006软件通过。#582保持OPEN，Plan active、capability idea/last_verified=null。

## In-Progress

当前synthetic-only软件交付供Owner接受；发布范围未授权。actual延期不归入Done，历史候选验收不计本轮通过。

## Verification and provenance — #587历史核心轮次，当前CLI见T-006

- 实施来源：Codex；Subagent dispatched：NONE；method：red-green。
- Tests：tests/unit/test_eval_core.py、tests/bdd/data_agent/evaluation/test_evaluation_bdd.py。
- Evidence：[核心验收](evidence/reports/2026-10-12_offline_core_acceptance.md)、[BDD](evidence/bdd/2026-10-12_core_scenarios_pass.md)、[合成回放](evidence/reports/2026-10-12_synthetic_replay.md)。
- PR：#587；核心／测试与文档已在007820e／3dd6b6b提交。公开API修复的提交与CI结果见最新证据；所有关联Issue状态未改，不关闭#582。

## Anti-Backlog

不做live采样、LLM judge、定时／CI blocking、waiver翻转、target runtime／原dataset改造或服务连接。

关联：[design](design.md)、[requirements](requirements.md)、[runbook](runbook.md)、[Plan](../../../plans/[PLAN]_582_offline_eval_runner.md)。
