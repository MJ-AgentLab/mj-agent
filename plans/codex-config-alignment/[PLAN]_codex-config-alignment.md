---
type: plan
summary: 对齐mj-system的Codex项目配置结构并评估九个SSH历史入口
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: active
track: engineering-workflow
---

# Codex 配置结构对齐与 SSH 评估

## 原意、基线与范围

原意正本为本旁聊Owner请求：“按照上述结构对齐，并评估为mj-agent配置以下mcp，让codex可以连接”，具名入口为cloud、runner-lan/runner-wan、test-lan/test-wan、prod-lan/prod-wan、dgx-lan/dgx-wan。此前Owner采纳的结构是项目配置主要保留MCP，审批/沙箱取实际宿主设置，退出项目hooks/rules自动加载及专属加载取证要求，保留数据、秘密、Git/Owner与平台边界。退出自动拦截不等于AGENTS或CI提供等价事前强制保护。

代码基线1022610eb4d0ada6352312e080965eeb8afe94ee；已完成608主题不重开。当前无主要Issue/PR，不猜编号。工作树为D:/workspace/10-software-project/projects/mj-agent/maintain/codex-config-alignment，分支maintain/codex-config-alignment。原develop和其他任务不写入。

实施仅本地配置/检查器/相应测试/当前政策技能契约文档。Owner于2026-10-29明确“执行B”：增加一个ssh-manager，全部9历史入口按既有账户接入，含cloud root及生产。原8项保持，加上SSH共9项MCP；仅凭据名称复用，不解密/复制秘密，不改个人配置。可做本地模拟MCP启动/握手，真实主机连接/远程命令不在本轮执行。旧ADR和验收记录不改成PASS。

## 可观察AC与验证

- AC1：当前项目config仅声明原8项与B决定的1项ssh-manager，共9项MCP；没有项目审批/沙箱覆盖，无个人配置写入。
- AC2：项目自动hooks/rules退出；旧软件诊断/测试资源有明确历史用途，默认配置检查不再要求宿主守卫加载取证。
- AC3：V11仍检查MCP用途/按名凭据与合法结构；错误、间接文件或禁入服务继续失败，不输出秘密。CI不靠跳过错误或默许白名单外服务通过；只增加Owner已决定的具名SSH。
- AC4：普通Git工作流、Owner接受、App发布与业务/秘密边界保持；无项目自动拦截的局限真实说明。
- AC5：当前政策、技能入口、消费者/合同与检查器一致；原历史拒绝/UNKNOWN保留；独立可信门禁等延期不被冒充完成。
- AC6：SSH为1个MCP、9入口、5类主机/5组变量；按Owner B选择配置全部入口/既有账户，明确通用远程执行和cloud root/生产权限影响，不读取凭据给模型。
- AC8：SSH启动自包含且依赖锁定，仅列出/单目标执行工具；未知服务/内联密码、缺凭据、未知或错误主机密钥、超时/取消/输出上限有离线负例。实际Codex发现、逐主机认证与命令结果单列未测。
- AC7：适用离线回归、文档、native与类型/格式检查有本轮真实结果；未测/依赖和独立核验状态分列。

## 授权、风险与停止

Owner已授权结构本地对齐、SSH评估及后续方案B的本地配置/依赖安装/准入同步和模拟验证。退出具名项目载体.codex/hooks.json与.codex/rules/mj-agent.rules属于已采纳结构；两者原Git字节由基线提交恢复，删除前核真实目标、跟踪/改动和重解析点，不清理目录或其他内容。最初仅本地准备；Owner随后明确“提交PR”，授权本主题在当前worktree暂存/提交、推送并向MJ-AgentLab/mj-agent的develop创建PR，不授权merge、账户/个人权限变更或真实主机连接。CI工作流发布所需临时Workflows write及本任务Gitee例外尚需具名决定，依赖步骤先保留待答。B允许的账户范围不等于远程动作授权。

旁聊禁止使用子Agent，故本地自检不冒称独立核验。正式交付前需在允许独立核验的主任务完成相关审查及Owner准确版本接受；主Plan保持active。实际技术拒绝只停受影响步骤并保留原错，不换工具或改配置绕过。

## 依赖、交付与恢复

先保留旧守卫的合成fixture，再以新配置正负例红绿验证；同步当前消费者，历史记录保持。SSH评估见 [评估报告](./[ASSESSMENT]_ssh_mcp_access.md)。MCP信任、服务连接和远程运行分开；新会话MCP加载需正常宿主验证。

恢复为基线Git文件与本分支实际diff，不涉及服务器、凭据或数据恢复。状态为本地候选，AC1–6和AC8有静态/离线证据，AC7本轮结果见本地报告。独立核验、真实宿主发现/认证和Owner最终准确版本接受未发生；主Plan保持active，不以文件存在或方向选择推定完成。

## PR发布准备检查点

2026-10-29，Owner明确“提交PR”。远端develop以GitHub连接器回读为1022610eb4d0ada6352312e080965eeb8afe94ee，与当前基线相同；maintain/codex-config-alignment尚无远端分支/同分支PR。独立旁聊不派子Agent，自检/本地验证不认证独立审核。普通stage/commit/PR所需准备沿本次请求推进，merge及整体接受未授权。

既有App5284037、installation170545174的daily受控审计为EXECUTOR_VERIFIED，仅metadata read、contents/pull_requests write，单仓repository1172583390；短期token撤销CONFIRMED。候选包含ci.yml变更，当前无Workflows write，尚未尝试被预知不允许的推送；不会使用Owner/MCP身份替代或改权限绕过。准备候选提交和PR正文后，仅就本轮临时Workflows write及Gitee发布范围给Owner具体选项，旧任务授权不移用。
