---
type: capability-tasks
capability: data-agent.evaluation
state: draft
version: "0.3"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
---

# Tasks: Offline EVAL Replay

> Owner已集中授权独立离线核心编码、必要测试、Agent合成验收和回归报告。
> 核心已交付，CLI／actual延期；不修改既有runtime，不执行live或Git发布。

## Done — 本轮核心范围

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

## Backlog — 延期范围

### T-006 CLI与actual入口

- Priority：high；Linked REQ：REQ-001、REQ-006。
- 状态：DEFERRED_NO_IMPLEMENTATION。runner.py／公开main、普通文件读写、URL／UNC／秘密路径／重解析点拒绝、输入与报告防覆盖、CLI端到端及进程退出验证均未实现。
- actual采样、来源真实性、真实审阅、模型／数据库／runtime EVAL继续延期，不要求Owner代替Agent做技术操作。
- 触发：后续范围作具体授权且具备能力，由Agent实施与独立验证；严格条件不降低，不补假锚点。
- RED／GREEN：NOT_RUN。

## In-Progress

无核心编码剩余任务；延期入口不会被归入Done。

## Verification and provenance

- 实施来源：Codex；Subagent dispatched：NONE；method：red-green。
- Tests：tests/unit/test_eval_core.py、tests/bdd/data_agent/evaluation/test_evaluation_bdd.py。
- Evidence：[核心验收](evidence/reports/2026-10-12_offline_core_acceptance.md)、[BDD](evidence/bdd/2026-10-12_core_scenarios_pass.md)、[合成回放](evidence/reports/2026-10-12_synthetic_replay.md)。
- PR：#587；核心／测试与文档已在007820e／3dd6b6b提交。公开API修复的提交与CI结果见最新证据；所有关联Issue状态未改，不关闭#582。

## Anti-Backlog

不做live采样、LLM judge、定时／CI blocking、waiver翻转、target runtime／原dataset改造或服务连接。

关联：[design](design.md)、[requirements](requirements.md)、[runbook](runbook.md)、[Plan](../../../plans/[PLAN]_582_offline_eval_runner.md)。
