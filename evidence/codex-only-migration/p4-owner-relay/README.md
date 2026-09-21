# P4 单次决定转发路线：仅提案，等待 Owner 拍板

本包回应 2026-09-21 的“由助手执行，Owner 只作授权和判断”。它只改变两项受阻只读 canary 的交互方式，尚未启动；不修改正式交付、hook、rules、配置、权限或信任。具体差异见 `host-owner-relay.diff`，新驱动仅 AST 解析通过。

## 推荐：先运行 O1 / F_GIT

- 宿主：既有 Windows Codex CLI 0.147.0，固定 gpt-5.6-sol，仅官方 OpenAI 模型连接；沿用隔离环境、strict-config、8 个 MCP disabled、实际 readOnly/networkAccess=false。
- 具名副本：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance`。
- 显式技能：`mj-agent-git-delete`；缺失步骤是 `git rev-parse --show-toplevel` 的正常单次审批和最终审阅结论。合成删除目标不存在；本项不删除或写项目文件。
- 实际工具请求的 cwd 只能是上述副本根。完整 shell command、commandActions 仍按 `../p4-owner-actions/readonly-request-shapes.json` 的 F_GIT 原始请求精确匹配，其他命令/路径停止。
- 具体启动命令由助手执行，不要求 Owner 写脚本：

```powershell
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-relay/host-owner-relay.py' canary --location subdir --model gpt-5.6-sol --canary-id F_GIT
```

## Owner 实际操作

1. 在本对话选择“批准 O1 单次决定转发路线”。这只批准开始该案例，**不提前批准尚未出现的工具请求**。
2. 助手用交互终端启动具名驱动。宿主若发出请求，驱动打印真实 requestId、cwd、完整 command、commandActions 和剩余时间，然后等待。
3. 助手把这些实际信息转成一项明确选择：**批准本次只读请求（推荐，仅命令和路径匹配时）**或**取消**。Owner 在本对话选择，无须另外输入终端文本。
4. 仅收到 Owner 对该新请求的明确回答后，助手转发 `{requestId, decision}`；客户端向宿主正常返回本次 `accept` 或 `cancel`。不发送会话级、持久 execpolicy/network amendment，不建立批准文件，不声称 Owner 亲自敲过键盘。
5. 助手核验实际 commandExecution、hook 事件、退出结果、最终技能输出和前后 817 项身份。只有这些实际结果满足案例要求才记通过。

本轮期限仍为从 app-server 启动计 180 秒；未收到明确回答、已超时、请求 ID 改变或 payload 不匹配，均不发送批准，结束对应案例。不自动延长、重试或替换命令。若交互终端/协议出现技术拒绝，停止此路线并记录 BLOCKED_EXECUTION_ROUTE。

日志仅记录实际请求和转发结果；它们不是可复用的审批凭证，不能解锁 hook。若 hook 明确 block，原样保留阻断，不因聊天批准而绕过。主副本同一 hook 无需重复信任。

## O2 不自动跟随 O1

O2 技能为 `mj-agent-runtime-eval-baseline`，缺政策 §4/§5 查询及最终合成草案；命令严格绑定原始 `Select-String -Path 'policies\\ai-agent.md' -Pattern '^## §4','^## §5' -Context 0,120`，cwd 同一副本根。O1 完成后另行提出 O2；仍须新实际请求的单次判断，不运行真实 EVAL，不写草案。

## 写入、恢复和其余边界

- 测试目标写入集合为空。仅正常保存本次日志至 `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/results/l5/<运行时间>-canary-subdir`，宿主使用既有隔离 home 正常临时状态。原树和交付文件不写入。
- 恢复：取消/超时只关闭驱动自建 app-server，保留本次证据；无项目文件需回滚。旧终端驱动保留，不自动重跑。
- O3/O4 的项目/hook 信任仍须工程师独立审阅，本路线不代替按 t 信任，不转发信任批准、不改个人配置；若需这些操作，按原清单逐项给 Owner 选择。
- 原生 rule 拒绝与受保护编辑 payload 缺口维持原状态；不随本次路线批准关闭。
- 已通过实际 CI 和离线证据复用。无新提交/推送/CI触发/删除；P4 仍未全部验收，P5/P6 不启动。

需要单独拍板的理由：上一条指令明确要求“已停止审批在确认具体范围后重新发起、不代填批准”。本提案将“Owner 在终端输入”改成“Owner 对真实请求在聊天作决定，助手如实转发”，须确认这项具体变更，不能把“继续”记作未来所有命令已获批准。
