---
type: adr
domain: WORKFLOW
summary: 以任务授权自主交付和结果式接受替代固定人工停点，保留技术边界并明确过渡门禁风险
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
state: draft
decision: accepted
track: engineering-workflow
---

# ADR 042: Agent-first 软件交付治理

> Owner 已批准 Agent-first 交付改造计划并请求实施。本 ADR 记录该决定；写入、规则加载、平台配置、发布和最终接受的实际完成状态须分别留证。活动 `decisions/` 与归档命名空间已核对，042 未被占用。

## Context

固定阶段暂停、逐提交内容批准和必须由人执行 merge 增加常规构建介入，却不能证明功能正确。项目已有规格、工作流、技能、离线测试及 CI，可复用这些载体分别保存接受基线与授权范围。Owner 希望依据可用成果和可复现风险证据接受交付，保留深入技术审阅的权力。

## Decision

Agent 自主设计、实现、验证、修复并准备验收包；Owner 定义目标、作实质决定、明确授权及最终接受。Harness 执行必要门禁。保留阶段作为检查点，取消 stages 5/7/9/11/13 的固定人工等待。路径和历史风险 enum 用于定位影响，审批由实际语义、权限和风险变化决定。

任务可集中授权具名操作、对象及环境。在目标、对象、环境、权限和风险边界未实质变化且未撤销时复用授权。提交、普通推送、PR 创建和 merge 可列入同一任务授权；记录实际版本及内容用于执行核验，不要求每次内容更新重复批准。删除、权限变更及高风险不可逆操作须独立列明条件。

保留 SQL 安全不变量、业务库只读工具链、秘密保护、禁入 MCP 服务和禁止绕过技术拒绝。独立Agent先读取真实原生配置/守卫并复现负例，执行Agent随后仅经宿主正常机制启用本项目信任、核实际加载/canary；不改个人config、不扩大权限、不绕技术拒绝。不支持的步骤如实未验证。仅新建单仓mj-agent-delivery-executor App的私钥/短期token允许由受控后台创建、DPAPI保存、签名、注入和撤销；模型、聊天、日志不可见。现有应用/MCP/DB/个人秘密永不读取，该例外不扩大服务、权限或操作授权。四类 runtime 面和兼容契约的基线内实现可自主完成，提供行为及负例证据；安全语义、业务口径、外发边界、breaking 承诺、接受标准或必要门禁变化仍由 Owner 决定。

独立核验者从接受条件建立期望、读取真实成果并复现，按风险模拟相关角色，不规定真人专家或固定人数。协调者只在可清楚划分且并行有收益时委派，在真实支持档位和既定资源范围内选择、升级 effort；提高 effort 不扩大权限或更换模型。

支持单 PR、多个独立 PR及短期任务集成分支。分层关系登记精确 head/base；子 PR 集成不等于整体交付。有效平台批准、部署授权、实际运行验证和 Owner 接受分别记录。Owner在聊天对实际成果/SHA作批准或接受决定；Agent依该真实决定以不同于作者/最后推送者的Owner身份执行平台审核，补推须重新取得有效决定/审核，批准与业务接受分记。App作者/推送/PR/merge身份无Administration、Checks write和bypass。

## 定向替代与保留

| 来源 | 本 ADR 替代的活动解释 | 保留 |
|---|---|---|
| ADR-034 | 所有 runtime 修改逐写拍板、普通 Plan 必须人工批准 | 实质决定先准备可审阅方案；授权与技术执行路线分离 |
| ADR-040 / ADR-041 | 人工执行 merge、每次实际 staged/PR 内容变化自动失去普通任务授权 | 原生维护权、G1/G2、具体命令诊断、独立Agent信任/负例核验、正常宿主启用与拒绝不得绕过 |
| execution-loop / ADR-015 历史来源 | stages 5/7/9/11/13 固定等待 | 阶段身份、规格、验证、文档和反扫要求 |
| lifecycle / ADR-021 历史来源 | PR merged/Issue closed 自动表示 Plan completed | 工作文档状态及稳定路径；completed 改为 AC 满足、成果可用且 Owner 明确接受 |

旧 ADR 正文、归档件及历史执行证据不改写；活动消费方同步新规则，而非依赖新增 override 掩盖矛盾。

## 2026-10-12 执行主体修订（Owner Q4/Q5/Q6）

Owner明确取消工程师向导：全流程由Agent执行。原向导方案已superseded，仓外旧文件保留历史，不删除。平台对象、权限与规则沿用Q3，只改变执行主体；Owner仍对实质风险和实际成果/SHA作决定。新受控后台`delivery_executor.py`、实际注册/信任加载/平台审核/撤销未完成前不得PASS；缺能力或技术拒绝只阻塞相应步骤。

## Consequences

- 常规实施由 Agent 负责，Owner介入集中于实质决定及聊天中的版本批准/接受，Agent据真实决定执行有效平台审核。
- `ci`、`docker-build` 必需检查、schema/trace 非零失败及绑定版本的仓外证据须实际运行验证；文本和静态检查不能证明平台强制。
- 首期候选仍能修改自己的门禁定义。Owner 对门禁、保护和接受基线的人工审核是已接受的过渡补偿；独立受控核验系统尚未实现，不宣称具有防自降强制保障。
- actual 采样、部署自动化、实际恢复演练及历史 capability 证据迁移继续跟踪为延期；延期不计 PASS。synthetic 只证明软件行为。

## Alternatives considered

- 保留固定阶段与逐提交批准：增加人工介入，仍无法保证成果正确。
- 取消所有审批并以 CI 全绿表示接受：混淆操作授权、门禁和业务接受，削弱风险边界。
- 首期立即建设独立可信核验与部署系统：扩大权限和平台依赖；先完成有界离线试点及过渡控制，再按需要交付。

## References

- [AI 政策](../policies/ai-agent.md) §2/§4；[工作流](../sdd/workflows/execution-loop.md)；[生命周期](../sdd/lifecycle.md)。
- [Git 分支政策](../policies/git-branching.md)；[交付指南](../docs/guide/[GUIDE]_Agent_First_Delivery.md)。
- [ADR-034](ADR-034_HITL_Propose_Decide_Apply_Model.md)、[ADR-040](ADR-040_Codex_Only_Development.md)、[ADR-041](ADR-041_Command_Specific_Git_Execution_Policy.md)。
