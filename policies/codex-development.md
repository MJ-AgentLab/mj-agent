---
type: policy
domain: WORKFLOW
summary: MCP-only的Codex项目配置与按任务验证边界
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: active
track: engineering-workflow
---

# Codex 开发配置

Owner在本会话采纳向mj-system结构对齐。项目`.codex/config.toml`只维护获准MCP，审批/沙箱取实际宿主与会话条件，不写个人配置。项目不注册`.codex/hooks.json`、`.codex/rules/*.rules`或inline hooks，不要求为普通任务取得旧项目守卫的来源/hash/加载取证。基本项目信任及MCP加载、连接和功能验证仍按任务需要分别核实；不能仅凭配置文件或命令成功认定服务可用。

AGENTS/技能用于执行约束；适用测试、CI、平台保护和App后台各承担其真实检查。退出项目自动拦截是Owner已选择的治理取舍，AGENTS与CI不是全部本地操作的等价事前防线。业务只读链、SQL不变量、秘密隔离、worktree/显式base、具名删除、Owner准确版本接受与App发布身份继续按相应政策执行。结构对齐本身不扩大服务；Owner随后明确选择SSH方案B，定向准入1项ssh-manager及9个历史入口，形成9项MCP。biz×5与其他来源服务继续禁入。

V11继续阻断非法MCP声明、按名凭据违规和重新引入项目hooks/rules；V13仍为warning，检查此结构退休状态，不启用或认证宿主守卫。旧guard/approval诊断API只用于历史合成fixture和显式只读诊断，不自动执行；当前MCP-only诊断说明没有项目规则要求，不产生任务授权、宿主许可或拒绝解除凭证。

已发生技术拒绝仍按其实际来源和正常恢复证据处理，不因本政策或删除配置而自动重试。历史ADR/报告/UNKNOWN不改写；如需结束旧加载验收，由Owner明确调整该任务范围并保留替代关系，不能勾成实际加载PASS。

实现与首次本地验证见 [本轮Plan](../plans/P611-codex-config-alignment/[PLAN]_P611-codex-config-alignment.md)。候选已由PR611承载，尚未集成；独立核验/最终接受另记。

## SSH：Owner选择B

一个ssh-manager维护cloud、runner-lan/wan、test-lan/wan、prod-lan/wan、dgx-lan/wan九入口，绑定`.codex/mcp/ssh-servers.json`的既有主机/端口/账户；cloud为root，生产两入口启用。配置准入不授权实际远程命令、部署、重启、文件覆盖、生产写入或备份恢复。通用shell具有写能力，客户端限制和提示词不是服务器只读隔离；每项操作按目标、命令、资源、副作用及停止条件核任务授权。SSH不能绕biz工具链、读取数据库或远端秘密文件。

启动采用项目相对`.codex/mcp/ssh-start.mjs`与锁定依赖，只暴露ssh_list_servers/ssh_execute；不提供额外sudo、SFTP、转发、批量或DB工具，但shell自身仍能执行这些操作，故禁止把工具裁剪称为权限隔离。后台仅消费五个既有MJ_SYS_SSH_SERVER_{CLOUD,RUNNER,TEST,PROD,DGX}_PASSWORD过程变量；不读值给模型、不解密旧bundle、不改User环境、不回退应用.env或个人SSH配置/私钥。原六变量GitHub/memory维护脚本范围不变，五个SSH变量单独注入。

只用本机OpenSSH已存在的known_hosts做公开主机密钥精确比对，未知、不匹配、revoked或不支持的CA记录均拒绝；不自动接受、扫描添加或改写信任文件。缺凭据不尝试认证，9入口仍列出缺失状态。每次只连接一个具名入口，不自动重试或切换LAN/WAN。超时、取消、断连、超量输出都可能留下远程任务，先核状态再决定后续；关连接不证明远程命令已回滚。输出仅对已注入的五个密码字面值脱敏，不能保证识别远端任意其他秘密，因此禁止执行可能读取秘密的命令。

配置、依赖/协议握手、宿主发现、各主机认证和远程行为分别留证。--check只输出公开元数据/存在状态，不连接主机；静态PASS及变量存在均不证明可达或认证成功。
