---
type: adr
domain: WORKFLOW
summary: 采纳与mj-system一致的MCP-only项目配置并退出项目自动守卫
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: active
decision: accepted
track: engineering-workflow
---

# ADR-044: Codex MCP-only 项目配置

## Context

Owner要求简化配置/加载要求，明确采纳本会话结构对齐方案A。当前宿主守卫加载取证独立于代码验证，项目需要保持真实能力与开发成本一致。活动及归档编号已核044未使用。本ADR记录方向采纳，不代表本地最终实现已交付或获接受。

## Decision

项目配置仅含获准MCP，退出项目审批/沙箱覆盖、hooks/rules自动注册及普通任务的旧守卫加载取证前置。现行正文为 [Codex开发配置](../policies/codex-development.md)。定向替代ADR-040/041/042中要求项目hooks/rules持续存在/加载取证的部分，旧ADR正文及历史失败、UNKNOWN不修改。

旧守卫软件与合成测试保留为历史诊断资源，不能宣称当前宿主执行。平台保护、App后台、离线runner、业务/秘密/Owner决定和具名操作要求保持；结构对齐本身不扩大MCP。Owner随后选择SSH方案B，定向准入ssh-manager九入口/既有账户，含cloud root和生产；实际远程动作仍按任务授权，biz/秘密边界不扩。实现采用项目自有精简接口和锁定SDK/ssh2，严格比对known_hosts；不复用历史3.1.0自动接受主机密钥及dotenv行为。

## Consequences

无需为每个工作树启用自定义项目守卫；MCP仍需正常项目加载与按需连接验证。退出本地自动拦截具有真实保护损失，AGENTS/CI不是等价替代。独立技术核验与Owner准确版本接受在本地候选完成后另记；旁聊不派生Agent、不发布或修改主工作树。

## Alternatives

保留hooks/rules仅缩减取证仍有信任/维护成本；Owner已选择结构对齐。照搬mj-system全部MCP会扩大服务/数据权限，未由本次结构决定授权。
