---
type: adr
domain: WORKFLOW
summary: 移除项目 Git 审批规则，分离动作授权、有限命令识别和宿主实际执行限制
owner: ranzuozhou
created: 2026-09-22
updated: 2026-09-22
state: draft
decision: accepted
track: engineering-workflow
---

# ADR 041: 按具体命令判断 Git 执行条件

> 来源：[Issue #555](https://github.com/MJ-AgentLab/mj-agent/issues/555)。Owner 已批准完整 28 文件补丁，2026-09-22 已应用到 codex/555-command-policy 工作树；未激活目标会话规则或 hooks，真实链路验收仍待完成。

## Context

#558/#560 将 Git 发布交给项目 prompt，同时将 never 诊断为统一阻断。任务授权已明确时，这种绑定仍会形成不可申请审批的执行停点；本地 Git 清理也不应继承 Remove-Item 的规则结论。历史实施及拒绝/成功证据保持原样。

## Decision

删除项目 rules 的全部六条 Git/gh 条目：commit、push、PR create 的 prompt，以及 checkout -b、switch -c、PR merge 的 forbidden。不新增宽泛 allow，保留 Remove-Item prompt 和 psql/pg_dump/pg_restore forbidden。

Git/gh 的 G1/G2、人工 merge 和既有数据/秘密/受保护编辑边界继续由 hook 与政策承担。有限识别的发布命令仅输出 TASK_AUTHORIZATION_CONTEXT；未知命令仍暂停。支持具名常用参数、显式 refspec 与逐引用核验的批量远端删除，不开放 force、amend 或 shell 展开。

项目动作授权、逐命令规则匹配、有效会话模式与宿主实际执行能力分别记录。never 单独不阻断无项目规则要求的 Git/gh；无匹配不等于宿主允许。已知拒绝须按实际来源核验恢复，规则文件修改本身不证明目标会话加载或拒绝解除。不修改个人配置、信任、服务集合或自动激活 hooks。

## Consequences

- 减少项目 Git 规则与 never 的人工等待，已批准具体动作不重复授权。
- 移除 Git 规则后，G1/G2 与人工 merge 少一层项目 exec-policy 防线；必须保留 hook 正反例、政策自守和工程师独立加载核验。
- host、组织策略或其他来源仍可能审批或拒绝；静态诊断不能承诺免审批。
- 新规则与解析器、检查器、文档须成组审阅和回退；恢复旧 Git 规则也需要正常审阅，不能用作绕过实际拒绝的临时开关。

## Alternatives considered

- 保留 Git prompt、统一要求 on-request：不满足 Owner 选择的无项目强制审批方案。
- 增加 allow 或让 UNKNOWN 全部放行：削弱未知命令和安全边界，未采纳。
- 将聊天批准编码成 receipt：无法证明宿主批准或正确绑定范围，未采纳。

## References

- [ADR-034](ADR-034_HITL_Propose_Decide_Apply_Model.md)：保留 Owner 决策模型。
- [ADR-040](ADR-040_Codex_Only_Development.md)：保留原生资产维护权与业务边界。
- [计划](../plans/[PLAN]_555_approved_deletion.md) §11：本轮范围与证据。
- [政策](../policies/ai-agent.md) §4；[开发指南](../docs/guide/[GUIDE]_Developer_Onboarding.md) §6.6。
- [Git commit](https://git-scm.com/docs/git-commit)、[Git push](https://git-scm.com/docs/git-push)、[gh pr create](https://cli.github.com/manual/gh_pr_create)：参数依据。
