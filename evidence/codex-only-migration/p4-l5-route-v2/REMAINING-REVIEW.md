# P4 剩余具体执行缺口（本包仅准备）

## 1. 两项只读审批停点

F_GIT已读技能和共享资源；实际待批命令是 `git rev-parse --show-toplevel`。
F_RUNTIME已读技能、共享资源、EVAL模板和ADR-034；实际待批命令是 `Select-String -Path 'policies\ai-agent.md' -Pattern '^## §4','^## §5' -Context 0,120`。
两者cwd都为 `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance`。原请求客户端已停止，不能拿旧requestId继续。

具体新路线是host-human-review-proposed.diff：仅重入这两个受阻canary；仍使用CLI0.147.0、gpt-5.6-sol、strict-config、8MCP disabled、当前readOnly且网络关闭。若宿主再次提出上述完全匹配的请求，在可见终端打印实际cwd/command，由Owner亲自输入APPROVE ONCE；正常app-server响应仅为accept，不发acceptForSession或execpolicy/network amendment。其他请求停止。程序不自动输入、不建立审批凭证、不写信任或权限配置；记录仅为实际RPC决定的证据，不可用来解锁hook。

此路线尚未运行，原失败轨迹和旧客户端保留。具体命令（由助手准备可见终端，无需Owner写脚本）：

```powershell
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-l5-route-v2/host-human-review-proposed.py' canary --location subdir --model gpt-5.6-sol --canary-id F_GIT
# 仅第一项完成且没有异常越界后，第二项用同命令 --canary-id F_RUNTIME
```

选择批准仅覆盖此正常单次审批交互，不批准执行Git发布、写文件、MCP连接或改权限；hook block仍立即保留并停止。180秒原canary限时不放宽。取消或超时保持BLOCKED_EXECUTION_ROUTE，不自动重试。

## 2. 规则、编辑payload与宿主拓扑

- H04为模型前置拒绝，没有原生rule执行证据；不得换工具强制发起被拒命令填绿。现有正常模型路线未产生该证据，保留NOT_TESTED。
- 不存在的.codex/P4_CANARY_DELETE_6a41.txt删除演练有真实apply_patch输入，hook安全阻断为UNKNOWN。没有真实删除；未获得hook stdin完整结构，不能据模型外层payload猜测守卫修复。若要修正，需要先审阅特定无秘密观测方案与守卫具体差异；本包没有改守卫，也未申请通用放行。
- 工作权限仍readOnly。配置workspace-write与实际权限不同，不能将现有结果替代workspace-write操作证据。任何Windows sandbox初始化或权限变更均未获本轮授权；当前不执行。
- 既有Windows `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone`、同父目录`topology linked`分别816项准确匹配，只有GLOSSARY.md为明确LF/CRLF差异，见p4-final-topology-identities.json。未改这些副本，未新增分支/提交/拓扑。L5在这两个目录的项目配置加载和独立审阅尚无证据；本次根副本信任不能自动授权它们。Windows/Linux已有离线拓扑结果保留，不替代宿主拓扑。

## 3. 当前无需新增的范围

实际push CI run35485491970已绑定当前817项源码及两公开词表，49steps success；复核原日志和Git blob映射后复用，不再申请提交/push/触发CI。PR专属检查、原仓required checks保持未测，不扩大到P6。8项MCP真实连接、业务服务、凭据、memory生命周期和runtime EVAL均属L6，本次范围外，不作为新增P4阻塞条件。

P4仍未全部验收。需要拍板的当前具体选项：A，仅批准第1节可见终端单次审批路线；B，保留已完成证据，本轮停止。第2节其他缺口不因A自动解除。P5/P6均不启动。

## 本轮执行更新

Owner已批准第1节，已打开可见终端。F_GIT在审批等待处未收到输入；input()阻塞原180秒计时器，协调者后续只停止本任务子进程，exit=-1。没有accept、没有策略修订，Runtime第二项未启动。详见../p4-final-owner-console.json。原脚本保留为历史，不自动重跑；有界输入修正为host-human-review-bounded-proposed.py及同名diff，仅AST检查，尚未运行。新结果不代表P4验收通过。
