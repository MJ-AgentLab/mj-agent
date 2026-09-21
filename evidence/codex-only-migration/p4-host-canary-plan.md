# P4 宿主 canary 待执行清单

状态：`NOT_TESTED / UNMET_DEPENDENCY`。这是具体验证输入，不是信任激活、权限调整或运行通过记录。

执行路线：`BLOCKED_EXECUTION_ROUTE`，仅指L5尚缺满足本轮约束的已审阅宿主路线；未观察新的技术拒绝，不改变P3 U04的`MANUAL_ROUTE_EXECUTED_VERIFIED`。

## 已绑定目标

- 独立副本：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/native acceptance`。
- 817个初始交付文件及来源摘要：`p4-copy-manifest.json`。
- 两文件最小修复及更新后身份：`p4-minimal-fixes.json`；其余交付文件保持原摘要。
- 原树188项应用身份：`p3-format-completion.json`；本轮源身份：`p4-resume-entry.json`。
- 实测命令行版本：`codex-cli 0.147.0`（只运行version/help及离线规则求值，不启动模型）。

## 执行前尚缺

工程师独立审阅此副本的项目与hook信任；当前没有该副本的信任或宿主加载证据。
可用宿主路线还须保证无秘密、无项目MCP/外部服务连接、无真实业务副作用。
正式配置含8个MCP启动定义，直接启动新宿主可能启动npx/uv工具或服务；不能靠一句提示词阻止启动。
本轮不改个人配置、不激活hooks、不使用bypass/ignore-rules、不切权限模式、不制造审批凭证。
只读CLI help并未证明 `debug prompt-input` 或新会话启动无MCP副作用，因此没有试运行它们。

## 场景及可观察证据

| 场景 | 无业务副作用输入 | 必需观察 |
|---|---|---|
| 根与子目录发现 | 宿主分别以副本根、`tests/unit`为cwd，仅读指令/技能目录 | 实际加载的根/局部AGENTS路径、37技能名称/路径、版本与时间；不得用文件存在替代发现事件 |
| doc族显式调用 | `mj-agent-doc-validate`：仅读已有README，报告格式检查，不修改文件 | 加载技能/共享说明并在本任务返回；实际工具轨迹 |
| flow族显式调用 | `mj-agent-flow-scope-drift`：只审本轮两文件修复与计划2.4 | 正确范围、证据和返回点，不进入Git交付 |
| git族显式调用 | `mj-agent-git-commit`：仅拟两文件message，不暂存/提交 | 报告未执行Git写操作；真实调用轨迹 |
| infra族显式调用 | `mj-agent-infra-storage-stack`：仅根据本地公开源码说明memory结构 | 缺服务能力如实标注；不连接DB、不备份或写入 |
| runtime族显式调用 | `mj-agent-runtime-eval-baseline`：仅说明既有公开EVAL依赖及未测项 | 不修改runtime正文、不编造测量、不触外部服务 |
| 近邻误触发 | 只要求解释函数，不请求提交或PR | 不误调用发布/清理流程 |
| 允许/拒绝 | 宿主自己的无副作用hook/rule模拟入口，对git status、git push、保护路径编辑、删除payload作决策 | 实际宿主已加载的规则/hook来源与决策；必须保证模拟不会执行目标动作；离线直接handler调用只能算L3 |
| 异常与重入 | 损坏payload、重复同一只读请求 | fail-closed及无重复写操作证据；不放宽边界 |

如宿主没有能保证无副作用的模拟入口，保护/删除场景保持未测，不发出真实破坏动作来赌hook会拒绝。
`execpolicy check` 与直接stdin调用guard仅作本地组件证据，不抵充宿主激活/实际拦截。

## Git拓扑与平台缺口

本副本只有临时Git索引，没有提交或远端。正常clone/linked worktree需要可检出的提交。
当前禁止提交，且原仓历史含排除的秘密包与旧客户端；不把原仓整个clone进来，不用commit-tree变相绕过。
若需补做这两个交付拓扑场景，需现成、无秘密且内容可核验的本地已提交交付源，或Owner另行明确测试路线。
已有fixture-runner测试创建的极小合成仓仅证明该工具行为，不代表817文件交付的clone/linked-worktree验收。

Windows根/子目录/含空格路径的组件验证另记 `p4-path-and-rule-checks.json`。
WSL只枚举到`docker-desktop`；不将其当普通Linux验收环境，也不启动容器或下载发行版。
Linux CI及其他平台没有执行证据，仍为`NOT_TESTED`。
