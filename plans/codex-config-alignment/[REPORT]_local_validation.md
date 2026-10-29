---
type: report
summary: MCP-only结构与SSH方案B本地候选、模拟验证及真实连接未测边界
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: completed
track: engineering-workflow
---

# 本地实现与验证报告

## 候选与交付范围

基线1022610eb4d0ada6352312e080965eeb8afe94ee；工作树D:/workspace/10-software-project/projects/mj-agent/maintain/codex-config-alignment、分支maintain/codex-config-alignment。成果为未提交的本地diff，不是已发布版本；本报告completed只表示本地实现/验证记录已交付，主Plan仍active。

结构对齐保留原8项MCP，后续Owner明确“执行B”，另增ssh-manager共9项MCP；移除approval_policy、sandbox_mode及project_doc_max_bytes覆盖。两项旧自动载体在核跟踪/无改动/普通文件后退出，原内容保存为固定合成fixture，基线Git对象仍可恢复。旧诊断软件不注册为自动hook。CLI对当前MCP-only结构不要求旧加载取证，实际宿主限制和MCP运行状态继续分列。

当前AGENTS/政策、相关Git/文档技能、模板、MCP设计/runbook、消费者和V13标签同步；V11仍阻断非法MCP及重引入扩展，V13 warning姿态不变。ADR-044记录Owner采纳方向，不改写ADR040/041/042及旧UNKNOWN。B变更前按canonical算法复算8个infra技能的16个hash及8套section heads一致；随后定向修改env-setup和storage-stack两项旧准入/计数说明，成组更新对应description/body hash与frozen_at，section heads保持，其余6项不变。

现行执行suite与迁移清单的两个旧自动载体输入路径改为legacy fixture；未来执行按新版本绑定。20个历史证据文件、历史输出/基线仍保持原字节，原验收不提升为actual或来源认证。变更没有业务runtime、数据库、生产资源或秘密操作。

## 本轮真实验证

Windows、复用develop/.venv与既有uv.lock；uv --frozen --no-sync；pytest只经scripts/sdd/run_offline_pytest.py。

- RED：新MCP-only正例1 failed、2 passed；旧检查器要求权限覆盖与原自动守卫文件，暴露预期差异。
- GREEN：新profile、legacy诊断、native scope、Git命令政策共145 passed。
- 全量unit首轮：1939 passed、2 failed、2 skipped、30 subtests passed，207.50s。失败为旧Remove-Item前置断言及当前suite引用退休路径，均有明确差异来源，不是宿主技术拒绝。
- 局部修复后：Git action、legacy suite及MCP governance BDD共47 passed，16.26s；包含20份旧证据完整性核验。该检查点保留首轮失败及局部恢复记录；后续B回归另在下方记录最终全量结果。
- Ruff全仓PASS；mypy src/mj_agent 57源文件PASS。
- 当前native profile、native entries/consumers/skills、7项capability contracts、loop section refs均PASS或STATIC_PASS；agent.contract检查无该类型为N/A，不伪造存在。
- Frontmatter、working目录/深链接、A4 strict wikilinks、git diff --check通过。静态通过不等于MCP连接或真实宿主运行验证。

两个SKIP分别为Windows不能创建真实symlink和非Windows event-loop用例，不计PASS。第三方Pydantic/gherkin弃用warning保留，Python依赖未变；SSH另新增锁定Node依赖。

## SSH方案B与本轮追加验证

九入口评估与Owner的B选择见 [SSH评估](./[ASSESSMENT]_ssh_mcp_access.md)。已增加1个MCP、9入口、5组变量的自有精简实现，保留历史账户含cloud root及生产；配置准入不授权实际命令。政策/合同/V11严格白名单与BDD同步，不导入biz或其他来源服务；原六变量解密维护脚本不扩容。只暴露列出与单目标执行两工具；通用shell仍能写，不能称为只读隔离。

历史3.1.0源码发现known host未比对指纹、未知host默认接受，以及包.env读取；故未部署该包。使用项目自有启动/协议代码与锁定@modelcontextprotocol/sdk 1.32.2、ssh2 1.17.0，完整npm lock/integrity，安装禁lifecycle scripts。通过OpenSSH既有known_hosts精确比较原始主机key，不自动接受、扫描添加、覆盖、降算法或切换入口。输出限制64KiB、30秒总时限，超时/取消/断连等远程状态未知；五个注入密码字面值脱敏不等于能识别任意远端秘密。

- Node RED：首次新测试因尚无实现模块失败，保留红态；随后实现并验证。
- Node GREEN：npm test为10 passed，包含纯模拟SSH客户端、原始key不符/未知key/撤销记录、缺凭据、命令非零、超时/取消、输出上限、已知密码脱敏、带空格cwd与stdio initialize/tools/list/安全调用。未打开远程socket或执行真实主机命令。
- npm ci --ignore-scripts --no-audit --no-fund安装102包；npm audit --omit=optional --audit-level=high当次报告0 vulnerabilities，不认证未来无缺陷。
- B后Python目标回归：194 passed（24.64s），覆盖当前/legacy/native scope、Git政策、legacy suite与MCP治理BDD。
- B后最终全量unit：1943 passed、2 skipped、30 subtests passed（208.08s）；无失败。两项SKIP仍为真实symlink及非Windows event-loop用例，不作通过。
- B后Ruff全仓、mypy 57文件、原生profile/entries/consumers/skills、G1/G2/G3各7P/0F、frontmatter 167文档、working目录/深链接、A4 strict链接、loop 21节、git diff/cached --check均通过。
- 跨仓引用检查warning：13处/10文件/43扫描文件；以主develop同检查只读回核为同一计数，保留原warning，未作无关清理。
- CI加入Node 22及相同离线Node测试，本轮未发布或运行远端CI。

实际--check只输出公开元数据和状态，五组过程变量均存在，known_hosts文件存在；未打印变量值、读取OS凭据库/应用.env/私钥或更改User环境。以上不证明九个目标都有可信key、当前网络可达或账户有效。

旁聊禁止子Agent，独立核验未执行；本地自检不代替独立核验或Owner准确版本接受。截至本地验证交付检查点，尚未commit/push/PR/merge，未申请Workflows权限，未改主develop、个人配置或其他任务；后续Owner已明确请求“提交PR”，发布准备状态另见主Plan检查点，未预记成功。当前Codex会话未动态加载新增MCP；需在此工作树的新会话按正常宿主机制核工具发现，逐主机认证与固定命令仍NOT_TESTED。正式集成须在允许独立核验的任务完成审查和准确版本决定。

## AI自检（提交前，区别于本地验证）

实际diff与结构对齐/B决定一致，原生配置/守卫退休、检查器及当前政策/合同需原子同步，故不按文件数量机械拆出不完整中间版本。本次为单一maintain主题，采用infra类型、省略混合scope。运行时skill/prompt/catalog、SQL/DB与Docker均无改动，5a–5d反扫不触发runtime EVAL或业务schema校验；历史状态与20份证据保持。新Node安全用例纳入既有ci作业，不修改required checks清单或continue-on-error姿态；V13仅改显示名称，继续warning。

12项自检覆盖模块边界、数据来源、公开固定SSH元数据/无秘密值、文档/INDEX/AGENTS同步、infra与maintain类型匹配、scope、双段记录、CHANGELOG、完整PR模板、旧引用与runtime EVAL适用性。公开主机IP/端口/用户来自Owner选择的B清单，明确作为连接元数据保留，不冒称零IP文本；实际凭据仍仅按名注入。GO仅为本地提交候选结论，独立审核、发布临时权限、真实宿主加载和主机认证均不由自检授予。
