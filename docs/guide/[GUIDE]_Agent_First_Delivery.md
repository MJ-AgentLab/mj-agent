---
type: guide
domain: WORKFLOW
summary: 使用接受基线、任务授权、独立核验和可恢复证据自主交付 mj-agent 软件
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
state: draft
track: engineering-workflow
---

# mj-agent Agent-first 交付指南

> **适用范围**：mj-agent 工程交付与治理改造。
> **目标受众**：Owner、工程师、执行与独立核验 Agent。
> **版本**：v0.1 草案。
> **最后更新**：2026-10-12。
> **规则依据**：本项目 ADR-042 及现行政策。
> **关联文档**：[[policies/ai-agent|AI Agent Boundaries]]、[[policies/git-branching|Git Branching]]、[[sdd/workflows/execution-loop|Execution Loop]]。

## TL;DR

阅读约 6 分钟。用既有任务记录分别保存接受基线和动作授权，Agent 自主构建/验证，Owner 作实质决定并接受成果；平台前置不足时记录真实状态。

## Prerequisites

读者应了解本项目永久数据与秘密边界，并能定位任务 Plan、政策和接受证据。工程师负责信任加载、秘密维护及具有权限的专用平台路线。

## 目录

- §0 适用场景
- §1 启动与自主推进
- §2 PR 与执行身份
- §3 启动前置与平台核验
- §4 独立核验与验收包
- §5 检查点、恢复与接受

## §0 适用场景

用于边界明确的软件交付试点、治理迁移和交接恢复。Humans steer. Agents execute. Harness assures. 本指南连接已有记录与规则，具体行为以政策、契约和任务接受基线为准。

## §1 启动与自主推进

在 Issue、Plan 或 capability tasks 中分别记录接受基线与执行授权。接受基线包含目标、使用者、范围、可观察 AC、必要运行条件、风险及延期；授权包含允许动作、精确对象、环境、权限、副作用、资源限制、失效及停止条件。普通技术选择、测试安排和局部修复由 Agent 决定；实质取舍先给具体选项及推荐理由。

技术权限、工具存在或 CI 通过不产生授权。授权未撤销且目标、对象、环境、权限和风险边界未实质变化时复用。普通代码内容更新仍需核验实际 diff/SHA，但不自动要求重复批准。具名删除、权限变化及高风险不可逆操作单列控制条件；秘密和 biz 旁路始终禁止。

## §2 PR 与执行身份

小任务用单 PR；可独立交付的单元用多个直接入主线 PR；强依赖任务用 `feature/task-<任务标识>-integration`。任务记录登记每条精确子 head → integration base、预期贡献和最终 base，创建命令显式传 base。集成分支验证累计差异与组合 AC，子 PR 已合并只表示候选集成。实施前核实平台规则、CI触发及merge是否导致部署。历史release develop→main是独立发布流程，须Owner接受、具名发布授权及未来规则映射；当前有限解析器不声称支持。

专用执行 App 仅安装本仓库，日常无 Administration、Checks write 或 bypass。Owner 使用不同于 PR 作者和最后推送者的身份提供有效批准，依据成果及风险证据决定；补推须重新取得平台有效审核。治理交付所需 Workflows write 属临时、仓库全域权限，工程师结束后移除该权限、吊销 token 并关闭临时通道。Agent 不创建或读取秘密，不代为激活信任。

平台尚未配置或宿主未加载时记录未验证/依赖阻塞，不能以文件修改声称完成。首期门禁仍可能由候选自身降低，Owner 对门禁、保护及接受基线的人工审核提供过渡补偿；独立受控强制核验系统延期。

## §3 启动前置与平台核验

1. Owner 成组审阅 `.github/agent-first/` 的 App manifest 和 develop/main/task-integration ruleset，核实际必要检查、最后推送审核、讨论解决、禁止force/bypass与merge副作用。准备文件不表示平台已应用。
2. 工程师独立注册专用 App、仅安装于本仓库、维护短期安装身份。日常仅必要contents/PR权限；本次Workflows write为明确临时、仓库全域权限，不声称按文件技术隔离。私钥/token不入聊天或日志，Agent不代维护秘密。

   Manifest 的 webhook 已关闭，URL 为保留的 `invalid.invalid` 占位地址，用于满足对象格式；不表示接收端存在或注册已获 GitHub 接受。工程师手工注册时保持 webhook 关闭。[GitHub Manifest 参数](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest#github-app-manifest-parameters)。
3. 规则应用需要另核具体平台操作授权及具备权限的工程师路线，不把执行App升为Administration或加入bypass。日常执行身份与Owner有效审核身份分离；末次推送后重新取得有效审核。
4. 工程师独立审阅原生配置/守卫成组差异，确认目标会话实际加载和支持的canary；没有独立加载证据标NOT_TESTED，Agent不自动信任/激活，也不改个人配置求通过。
5. 从项目根运行 `uv run --frozen --no-sync python scripts/sdd/check_delivery_platform.py` 只核准备文件；加 `--inspect --repository MJ-AgentLab/mj-agent` 只读核远端。CONFIG_VALID是准备格式，不能替代安装身份、宿主加载或真实平台canary。
6. 任务记录精确具名的受保护临时分支/PR后，才按授权核单PR、独立PR与子head→integrationbase模式，验证旧批准被补推失效、最后推送审核、红灯/讨论阻断和无bypass合并。未执行记录NOT_READY/NOT_RUN；清理独立列对象和授权。
7. 治理交付结束，工程师移除App的Workflows write、吊销临时token并关闭临时通道；分别核权限撤回及凭据不可再用，不打印凭据。撤回未完成仍作为交付待办。

分层路由在既有Plan放 `agent-first-routes` 块，准确字段与例子见Plan模板；前置未满足保持active=false，名字及登记本身不生成操作授权。新证据artifact只记录授权范围观察，不认证授权来源。

## §4 独立核验与验收包

核验者读取真实 diff、产物及基线，独立建立期望并复现关键检查。按风险覆盖工程、领域、Prompt 和供应链视角；不规定真人或人数。委派包含目标/AC/决定位置、输入范围依赖、真实工作区及比较版本、产物及证据要求、授权资源停止条件和返回点。并行写使用独立工作区或明确文件归属，共享资源写由协调者排序。

每个交付单元提供成果使用入口、逐 AC 预期/实际、版本环境时点、复现方式与证据位置、未实测/延期、风险与恢复、待决定事项。CI 仓外 artifact 绑定 head/base、测试版本、产物/输入/依赖摘要、环境、命令退出及逐 AC 状态。基线、产物或环境变化后重判证据有效性；HTTP 成功、命令成功、零行和 workflow 结束不独自证明业务正确。

本次治理软件交付执行新的证据要求，并设计#582治理证据格式。Owner已将#582 CLI实现/commit转交“整理 #564 EVAL 承接方案”，新CLI接受基线与实际交付由接手会话维护；原边界和未提交材料保留，转交不计交付PASS。历史 capability 逐步迁移；synthetic 和虚构 actual 条件只证明离线软件行为，不产生真实 runtime 来源或基线。缺少非核心能力可以延期对应入口，核心自身 AC 通过后分段交付；延期影响整体基线时由 Owner 决定。

## §5 检查点、恢复与接受

阶段完成、集成前和交接时，在现有记录保存目标/AC/授权、workspace/ref/SHA/集成状态、证据、在途动作、失败未知延期、下一步及停止条件。换窗、压缩及再委派后先读取记录并核实现状；超时或结果未知先对账运行状态和副作用，再决定是否重试，成功动作不重复。

分别表达候选已集成、已验证、已交付、待 Owner 接受、已接受、部分完成、延期、失败和未知。Plan 只有对应接受基线满足、成果可用且 Owner 明确接受该版本后才标 completed。仓库批准、部署授权、实际运行验证和业务接受各自留证。

局部可逆动作在授权内完成；共享环境核对目标与并发。恢复随风险使用回滚 PR、备份恢复、补偿或降级；存在文档不等于恢复已验证。actual 采样、部署自动化、独立可信核验和实际恢复演练为延期。评价时记录 Owner 常规介入、周期、缺陷返工、门禁负例、证据完整性、恢复结果及资源消耗。

## 关联文档

- [ADR-042](../../decisions/ADR-042_Agent_First_Delivery_Governance.md)
- [Plan 模板](../_templates/TEMPLATE_PLAN.md)
- [开发入口](../../AGENTS.md)

## 更新记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-12 | v0.1 | 建立任务授权、独立核验、仓外证据和平台启动指引；#582 转交另会话 |
