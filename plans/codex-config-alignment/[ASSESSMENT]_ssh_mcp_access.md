---
type: assessment
summary: 九个历史SSH入口的方案B选择、本地配置和未验证边界
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: completed
track: engineering-workflow
---

# SSH MCP 接入评估

## 结论与实际证据

技术上可以通过1个ssh-manager MCP注册9个入口，背后为5类主机/5组密码变量。初次评估检查mj-system的已提交配置、公开启动代码、静态主机清单字段及已安装软件代码；随后Owner明确“执行B”，已准备独立的本地实现并完成模拟MCP握手。未读取凭据给模型，未读OS凭据库、.env或私钥；未连接真实主机。

| 主机类别 | 历史入口 | 历史端口 | 工具变量名 |
|---|---|---|---|
| 云服务器 | cloud | 22 | MJ_SYS_SSH_SERVER_CLOUD_PASSWORD |
| Runner | runner-lan / runner-wan | 22 / 2201 | MJ_SYS_SSH_SERVER_RUNNER_PASSWORD |
| 测试 | test-lan / test-wan | 22 / 2202 | MJ_SYS_SSH_SERVER_TEST_PASSWORD |
| 生产 | prod-lan / prod-wan | 22 / 2203 | MJ_SYS_SSH_SERVER_PROD_PASSWORD |
| DGX | dgx-lan / dgx-wan | 22 / 2204 | MJ_SYS_SSH_SERVER_DGX_PASSWORD |

这些是既有工具变量的名称，不是凭据值，也不证明变量已配置或主机当前可达。LAN/WAN不是独立账户，自动回退和同时探测两端不默认启用。地址、端口和用户名绑定已获B选择的历史清单，保存在本项目ssh-servers.json；不从别名另猜生产身份。

## 可复用结构与边界

mj-system使用项目内Node启动入口、固定ssh-servers清单和空TOML基础配置；启动时清除继承SSH_SERVER_*再按具名变量生成可用主机，缺某组密码则不注册该组。已复用项目相对入口/固定清单/按名注入设计，mj-agent使用自有精简实现及锁定依赖，不引用mj-system工作树或用户插件缓存，不写用户级Codex配置。

当前安装的是@iflow-mcp/mcp-ssh-manager 3.1.0；本地registry声明ssh_list_servers、ssh_execute、ssh_upload/download/sync及额外sudo/session/group/database/backup等工具。它不是只读连接器，非root用户名也不能证明无sudo/写权限。cloud历史用户明确为root，其他账户权限未核。不能把只读标签或聊天指令称为服务器权限隔离。

历史3.1.0源码的SSHManager.connect对known host未比较指纹，对新host也默认接受；index.js还会加载包目录.env。故未复制或启用该包。当前ssh-manager为项目自有SDK/ssh2精简接口，依赖固定为@modelcontextprotocol/sdk 1.32.2和ssh2 1.17.0，含完整npm lock/integrity，npm ci禁lifecycle scripts。上游[ssh2 API](https://github.com/mscdex/ssh2/blob/v1.17.0/README.md)说明hostVerifier接收原始key，本实现与正常OpenSSH既有known_hosts精确比较；不接受/添加未知key，不读个人SSH config/私钥或任何.env。first-party-wrapper表示本项目启动/协议代码，不能据此认证第三方依赖无缺陷。独立复核仍待允许Agent的主任务进行。

## 权限变化与方案

初次评估基线禁止ssh-manager，结构对齐本身未解除禁入。以下A/B已呈现给Owner；Owner随后明确“执行B”，因此当前本地候选定向准入ssh-manager并同步检查器/合同/政策，共9项MCP。biz直连和秘密读取边界继续适用，不能利用SSH绕过业务工具链或读取远端.env。

- A（推荐首期）：登记全部9入口，仅启用非生产7入口；生产2入口保留未启用状态且不注入生产密码。cloud先使用经确认的受限账户，历史root不默认接入。首轮连接验证仅固定身份/主机名/系统版本等脱敏诊断；只暴露所需工具，额外sudo、传输、批量、DB/备份工具不默认提供。通用ssh_execute仍有写能力，不声称强制只读；实际远程操作按具名任务授权。
- B：统一启用全部9入口，沿既有账户及正常不透明凭据管线。须明确接受生产入口与cloud root的权限影响，首次连接清单逐目标列命令、资源与输出边界；部署、重启、文件覆盖、数据库和生产写入不由接入决定概括授权。

若Owner要求强制只读，需要受限服务器账户/服务端限制或固定诊断接口的独立具体方案，单凭现有ssh-manager配置无法保证。此为新的权限边界设计，不以临时客户端提示词实现。

## 接入验收与停止条件

分别验证静态清单和按名注入、Codex正常MCP工具发现、具名主机认证、固定命令结果；前一项通过不代替后一项。所有凭据仅由正常受控进程消费，模型不接触值；不读取既有凭据库作迁移。实际拒绝保留原错，不借LAN/WAN切换、替换工具或扩权限绕过。

本地B实现已准备，静态正负例、模拟协议和主机密钥/失败路径验证已执行，详见 [本地验证报告](./[REPORT]_local_validation.md)。当前过程五组变量均存在（仅布尔状态），known_hosts文件存在；不证明九目标各有可信记录、主机可达或账户认证成功。Codex当前会话未动态加载新MCP；真实宿主发现/主机认证/命令结果均NOT_TESTED。评估与本地配置记录completed不代替主Plan接受；不修改主develop，不发布。
