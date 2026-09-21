# P4 剩余 Owner 操作清单（2026-09-20）

本清单只覆盖 P4。下列“准备好”表示具名路线可供审阅，不表示已获实际审批或已验收。本轮没有重开旧审批、发模型请求、修改权限/信任、写测试目标或触发 CI。原树不暂存、不提交、不推送；P5/P6 不启动。

## 共同身份与边界

- 宿主：Windows Codex CLI **0.147.0**，固定 `gpt-5.6-sol`，仅官方 OpenAI 模型连接；8 个项目 MCP 完整定义显式 disabled，web_search disabled，实际 app-server/TUI 保留 `--strict-config`。
- CLI 绝对路径：`C:/Users/Admin/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe`。SHA256 `935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d`。
- 主验收根：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance`。
- 隔离宿主状态：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/isolated-codex-home`；沿用已登录状态，不读取、复制或归档认证内容，不改日常个人配置。宿主可能正常写此既有一次性状态目录。
- 原树：`D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration`。HEAD `20e2f24c352cf640d9dd33234b128ca897804b99`，索引为空且摘要不变。主副本和原树 817 项均复核通过。
- 所有新取证输出仅在 `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/results/l5/<运行时间>-...`；本仓新增审阅包/累计记录不属于测试目标写入授权。
- 主副本同一 hook 已由 Owner 信任，不重复操作。CLI 结果不代表 Desktop App；Linux CI 不代表 Linux Codex 宿主。

## 已准备好：O1 / F_GIT，只读单次审批

**技能：`mj-agent-git-delete`。** 已实际读取技能及共享边界；缺失步骤是根路径确认命令通过正常人工审批并返回，然后完成“为何不能删除”结论。合成目标不存在，也没有分支、合并证据或删除批准；本项不删除任何文件。

- 模型线程 cwd：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance/src/mj_agent`。
- 实际待批工具 cwd：上文主验收根；只允许 `git rev-parse --show-toplevel`。
- 预期：正常命令 exit 0，返回主验收根；记录对应 hook/工具事件及技能最终结论。若出现不同命令/路径、hook 拒绝或额外审批，停止，不改用其他路线。
- 文件差异：仅本包 `host-human-review.diff` 的取证驱动修正。逐案例匹配已观测的完整 shell command 和 commandActions；不把 Git 与 Runtime 两个许可混用。Runtime 原始请求的双反斜线按真实 JSON 保留，不做任意规范化放行。
- 恢复：项目文件无写入，无需回滚。Ctrl+C 或超时停止本次驱动及其自建 app-server；保留日志。旧请求已失效，不能重用 requestId。

Owner 准确步骤（确认 O1 后才由助手打开终端，也可自行运行）：

1. 在 PowerShell 执行以下脚本；不需管理员权限或 ExecutionPolicy Bypass。若脚本执行策略拒绝，报告拒绝并停止。
2. 核对窗口标题 `P4 F_GIT - one read-only approval`，准备好后输入 **START** 并回车。此时才启动模型，180 秒期限开始。
3. 出现 `OWNER REVIEW` 时核对 `case=F_GIT`、上文绝对 cwd、`commandActions` 中命令完全相同。完整 shell 包装同时显示，绑定见 `readonly-request-shapes.json`。
4. 仅此请求输入 **APPROVE ONCE** 并回车。不要选择永久、会话级或修改规则；助手不代填。其他输入取消，超时不发批准。
5. 等窗口显示退出码；无需自行判断 PASS，助手按实际工具/hook/完成事件核验。不要自动再次运行。

```powershell
& 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-actions/F_GIT.ps1'
```

## 已准备好：O2 / F_RUNTIME，只读单次审批

**技能：`mj-agent-runtime-eval-baseline`。** 已实际读取技能、共享边界、EVAL 模板及 ADR-034；缺失步骤是查询政策 §4/§5 并完成合成 EVAL 草案。此项不是运行真实 runtime EVAL，不写草案文件。

- 宿主、线程/工具 cwd 与 O1 相同。
- 唯一待批命令（双反斜线是原始 action 实际拼写）：

```powershell
Select-String -Path 'policies\\ai-agent.md' -Pattern '^## §4','^## §5' -Context 0,120
```

- 预期：命令 exit 0，只读已交付的非秘密政策；模型完成结构、缺失输入、审批及恢复边界说明，明确无真实数据集、模型评分或 EVAL 运行证据。
- 取证驱动、截止时间、恢复和停止条件与 O1 相同。O1 不自动启动或批准 O2。
- Owner 步骤：确认 O2 后运行下列脚本，标题须为 `P4 F_RUNTIME - one read-only approval`；输入 START，随后逐字核对实际 cwd 和上列命令，再亲自输入 APPROVE ONCE。不要将命令另贴到普通 PowerShell 执行来替代宿主证据。

```powershell
& 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-actions/F_RUNTIME.ps1'
```

**驱动验证边界**：本轮仅运行隔离的输入代码段和请求匹配判断：无输入超时、取消、Ctrl+C、退格，以及两项请求各五种错误输入均符合预期。测试没有连接宿主、发送批准或伪造 Owner 输入。真实终端有界等待尚未执行，不能写成通过。

## 已准备好：O3 / O4，两个拓扑的独立项目审阅

| 项目 | Windows 宿主绝对路径 | 具名启动文件 |
|---|---|---|
| O3 clone | `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone` | `T_clone.ps1` |
| O4 linked | `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology linked` | `T_linked.ps1` |

本轮已实际在每个拓扑的根、src/mj_agent、tests 查询：37 项目技能+6系统技能，errors=0；hook 列表为空、无 errors/warnings。该结果不等于 hook 缺失或已信任，具体项目层加载/信任尚需交互观察。两副本均为 816 项精确匹配，GLOSSARY.md 为已核实单一 LF/CRLF 映射；不写回对齐，不新增提交/分支。身份映射详见 `independent-verification.json` 和历史 `p4-final-topology-identities.json`。

**本次只请求具名路径的项目/hook 人工审阅，不自动运行模型用例。** 启动器沿用上述 CLI、隔离 home、完整禁用 MCP 和 strict-config；具体差异 `topology-owner-tui.diff`。不初始化 Windows sandbox，不改权限模式。任一技术拒绝停止该拓扑。

Owner 步骤（每项单独确认）：

1. 运行该项脚本，核对脚本打印的绝对目录，输入 START。
2. 仅若 CLI 出现该**准确路径**的项目/目录信任提示，由 Owner 审阅后选择信任。未出现不推定已信任；记录实际界面。出现管理员/安装/改权限/其他路径提示时停止并反馈。
3. 在 **Codex CLI 输入框**输入 `/hooks`。进入 PreToolUse 条目，核对来源为本项副本的 `.codex/hooks.json`，matcher `Bash|shell|exec_command|apply_patch|Edit|Write`、timeout 30 秒；解码全文见 `../p4-l5-route-v2/hook-decoded.ps1.txt`。
4. 该副本定义/启动器/守卫与主副本三项 SHA 必须一致；助手会在启动前再次校验。若需要新路径信任，由 Owner 亲自按界面 `t`；若已 Trusted/Active，不再重复。列表为空则如实记录，不改配置补出条目。
5. 留存该路径与 Trusted/[x]、Installed/Active 的无秘密截图；不输入业务提示。用 Ctrl+C 退出 CLI。助手再查元数据，只有加载/信任确认后才准备该拓扑必要的只读行为增量，不重跑离线测试。

```powershell
# O3，单独执行
& 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-actions/T_clone.ps1'
# O4，另行确认后单独执行
& 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-actions/T_linked.ps1'
```

预期是实际项目配置与 hook 来源可核，不以界面信任替代 hook 调用。恢复：退出本次 CLI，不修改拓扑文件/Git；本次人工信任仅存既有隔离 home，暂留作证据，不复制到日常 home。若 Owner 要撤销，须按实际 `/hooks` 提供的操作另行审阅，不擅删认证/信任记录。此处未承诺或执行一键回滚信任。

## 尚无可执行路线：不要求 Owner 笼统批准

### R1 原生 rule 的独立拒绝证据

H04 仅模型前置拒绝；H05/H06 为实际 hook 拒绝，不能替代 rule。当前没有已核实能安全取得独立 rule 事件的正常路线；不换工具强制执行被拒 Git 命令，不用手动 rule 检查填充实际宿主结果。Owner 当前无需在终端补执行命令。助手须先完成准确协议/事件诊断方案；如需改变输入或保护面，另交具体差异和恢复包。状态 `BLOCKED_EXECUTION_ROUTE`，无新增批准请求。

### R2 受保护编辑 payload 与写入边界

真实 Delete File 已被 UNKNOWN fail-closed 拒绝，外层 apply_patch 参数已保存，但 hook stdin 结构未取得；不能据此声称受保护路径识别通过或猜字段修改守卫。现有有效拒绝/恢复证据保留。

计划 §6.2 要求真实无副作用保护行为，并未要求全局开启 workspace-write；本轮不申请它，不以 Windows sandbox 安装或 Full Access 解决。以下只是**待方案完备后才可单项审阅的写入范围**，本轮不执行、不作为额外必需验收：

```diff
*** Begin Patch
*** Add File: C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance/.codex/P4_CANARY_BOUNDARY_20260920.txt
+P4 synthetic protected-boundary probe; no secrets or business data.
*** End Patch
```

目标必须事先不存在且非链接；只能请求宿主 apply_patch，预期明确受保护编辑拒绝、文件仍不存在。模型口头拒绝、权限层拒绝、UNKNOWN 各自单列，不得互相替代。当前没有准备执行驱动，不请 Owner 手动应用这段差异。若未来批准后保护意外失效，恢复仅限核验该绝对路径、且内容严格等于上面一行的合成文件，再由 Owner 认可的具名恢复动作移除；内容不匹配则停止。不得触碰现有 `.codex/hooks.json`、守卫、业务文件或原树。

## 无需 Owner 再操作的项目

- 实际远端 CI 已存在：[run 35485491970](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35485491970)，当前交付映射已核对；49 steps success，1051 passed/22 skipped。保留本地原始日志/树记录，不重发 CI、不新增发布授权。
- 原/主副本 817 项、已批准 P4 修复、P1 共享安全测试拆分以及全部历史恢复包保留；无需重放补丁。
- 主副本 37 技能发现、doc/flow/infra 三族、近邻、hook 允许/拒绝、错误恢复/重入的有效证据复用；不重跑无变化项目。
- 8 MCP 真实连接、业务服务、memory/凭据平台和真实 runtime EVAL 属 L6；本轮不把它们加入 P4 阻塞条件。
- 387 清理候选仍不可清理。Git HEAD 仅恢复提交基线；未提交 P0–P4 依原具名备份。此次记录改动的恢复源是 `.mj-agent-local/p4-owner-checklist/records-before.zip`（摘要见本包 prior-records.json），不用于恢复业务或交付文件。

**推荐操作顺序：先单独确认 O1；完成后确认 O2；再分别处理 O3/O4。** 每次确认仅覆盖具名路线启动，实际命令仍由 Owner 当场单次批准。R1/R2 不随任何 O 项确认自动获准。当前 P4 未全部验收，P5 `BLOCKED_PREREQUISITE`，P6 未启动。
