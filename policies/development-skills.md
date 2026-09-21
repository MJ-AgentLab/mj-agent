---
type: policy
artifact: development-skills
state: draft
version: 1.0
owner: ranzuozhou
created: 2026-09-18
updated: 2026-09-18
track: engineering-workflow
ai_visibility: source-of-truth
---

# 原生开发技能政策（P3 待批准草案）

本草案提取原开发技能规则的有效约束；必须与 ADR-040、根入口、infra 契约、检查器及 CI 一同批准和切换。当前不是活动规则。

## §1 三种技能来源

开发工作流位于 `.agents/skills/mj-agent-<group>-<verb>/SKILL.md`，由 Codex 发现，直接维护。
业务 runtime 位于 `src/mj_agent/skills/`，继续使用既有多字段 schema 与 `load_skill()` 去除 frontmatter 的契约。
个人或 marketplace 插件在项目治理范围外；不得为迁移导入其 MCP、配置或凭据。

## §2 开发技能 schema 与工艺

开发技能 frontmatter 只含字符串 `name`、`description`，严格 YAML，拒绝重复键；name 等于目录名。
description 保留正向触发与 `Do not use for:` 近邻排除，长度 200–1024；中文冒号为等价标点。
完整步骤、授权、异常恢复、完成判据和交接返回仍放在正文，不用发现层短描述代替流程。
工艺深度继续由 `docs/rule/[STANDARD]_MJ_Agent_Skill_Authoring_Craft.md` 规定。
本轮 37 个名字是迁移验收集合，不是永久禁止增添技能的数量常量。

## §3 Namespace 与资源

group 保持 doc、flow、git、infra、runtime；新增第六 family 仍需另行 ADR。
既有 family 内普通新增技能遵循任务授权、schema 和索引同步，冻结/保护面另按 §4。
索引是 `.agents/skills/SKILL_INDEX.md`；共享说明为 `.agents/references/execution-boundaries.md`。
相对资源从目标技能路径解析，`repo:` 路径从实际工作树根解析；缺资源即失败。
不生成第二份技能源，不引用候选目录、临时审阅脚本或旧客户端作为活动依赖。

## §4 Runtime 与 infra 冻结

runtime 家族仍是 propose→Owner 拍板→apply；技能调用本身不授权修改 src 的 Prompt、SQL、catalog 或 runtime skill。
infra 冻结合同位于 `capabilities/infrastructure/mcp-server-governance/contracts/development-skill.contract.yml`。
修改前复算旧 description/body 摘要；批准后对新正文、节标题及冻结时间成组更新。
算法、结构和必填字段见合同 header 与 `sdd/schemas/development-skill-contract.schema.json`。
`scripts/sdd/check_native_skills.py` 检查 schema、资源、索引及冻结摘要；不认证 Owner 批准。

## §5 A12–A14 与执行边界

- A12：开发技能 schema、命名、description、资源及冻结；原 V4 的全 WARN/未传 strict 不能冒充有效硬失败。新硬失败接入必须单列 Owner 门禁批准。
- A13：原生项目 config/hooks/rules 的权限与守卫人工审阅；秘密值不进入配置或日志，需批准动作保持 hook block。静态规则检查不等于完整沙箱或宿主加载。
- A14：MCP 服务集合、trust posture、凭据模式与启动器；治理 home 仍为 mcp-server-governance capability。既有服务用途不扩大，新的用途/服务需单独批准。

规范约束、机器检查、宿主能力和人工审查分别留证。聊天批准不等于 hook 解锁；没有已审阅路线返回 BLOCKED_EXECUTION_ROUTE。
禁止创建审批凭证、停用保护、改会话模式或换工具规避拒绝。项目/hook 信任由工程师独立操作，不由仓库脚本激活。

## §6 MCP 治理

项目 inventory 的维护正本为 `.codex/config.toml`；只承接既有 GitHub、Playwright、Serena 与 memory×5。
biz×5 和 ssh-manager 永久排除；biz 数据只能走 agent 的只读工具链，memory 不能充当 biz 旁路。
原有 trust posture 分级、降级条件、PR 声明和季度审计继续保留在 capability；本政策不另造治理平台。
缺凭据、服务、后台生命周期或平台能力时明确 UNMET_DEPENDENCY / NOT_TESTED，不用名称近似的工具充当等价实现。
