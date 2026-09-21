# O4 linked：具名审阅、离线环境与一次实际调用（待批准）

O3已实际完成根hook/tool canary。此方案仅将同一最小验证用于既有linked worktree，不重复离线测试，不新建worktree、提交或分支，不动其他工作树。

**唯一目标：** `C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology linked`。三项hook链已与原树核对；`.venv`当前不存在。原有linked `.git`连接保留，绝不替换、复制或重建Git元数据。

## 1. 助手打开具名终端，Owner亲自审阅

```powershell
& 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-owner-actions/T_linked.ps1'
```

终端标题为`P4 linked - Owner project/hook review`。Owner输入START，核对显示目录为上述linked绝对路径。项目/目录信任提示如出现，仅由Owner审阅并选择；未出现不能假定已确认。

在CLI的hook审阅界面选择Review hooks，进入PreToolUse具体条目；来源须为本linked副本`.codex/hooks.json`，matcher为`Bash|shell|exec_command|apply_patch|Edit|Write`、timeout30秒。完整解码沿用`../p4-l5-route-v2/hook-decoded.ps1.txt`，启动前再次核对定义/脚本SHA。Owner亲自按t信任当前单项；若已Trusted则不重复。核对Trusted/[x]及Installed1/Active1后反馈。助手不自动信任、不改个人配置/权限、不输入业务任务。若出现其他路径、条目或技术拒绝，停止该动作。

## 2. 信任证据复核后，助手执行已具名的离线准备

只有Owner实际审阅完成、只读API及当前文件身份复核通过，才继续。唯一新增文件范围为当前不存在的linked副本`.venv/**`：

```powershell
& 'C:/Users/Admin/AppData/Roaming/uv/python/cpython-3.13.5-windows-x86_64-none/python.exe' -B -m venv --without-pip 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology linked/.venv'
```

采用已核验Python3.13.5、白名单离线环境；不装pip/第三方包、不下载或复制缓存/主副本整个环境。创建前核对绝对目标不存在、非链接；记录实际生成文件/摘要及Git前后状态，与O3方法相同。若目标已出现则停止，不覆盖未知文件。

## 3. 单次模型canary

```powershell
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-O4-host/host-O4-status-proposed.py' canary --location root --model gpt-5.6-sol --canary-id O4_ROOT_STATUS
```

只在linked根通过宿主执行`git status --short`一次；CLI0.147.0/gpt-5.6-sol、官方OpenAI模型提供者、strict-config、8MCP disabled、隔离home、readOnly/networkAccess=false及180秒期限保持。实际差异见`host-O4-status-proposed.diff`，只将已验证O3驱动的目标和案例ID换为O4；目前仅AST解析，尚未运行。

预期：正确根AGENTS来源、项目技能与hook来源、真实hook调用、真实commandExecution exit0、实际状态输出及前后交付身份。已有迁移修复或换行状态如实保留，不为clean回滚文件。首个hook block或非预期审批/技术请求立即停止，不改命令、工具或权限重试，也不自动批准。

## 写入及恢复边界

- 除新`.venv/**`外，只保存本次日志到既有`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/results/l5/<时间>-O4-root-status`及宿主正常隔离状态；不写817交付文件或原索引。
- 正常Git只读命令可能刷新这个一次性linked索引统计，须记录实际变化，不动其提交/分支/远端。
- `.venv`原状态不存在；实际生成清单、来源和摘要是后续恢复依据。本轮不删除；未来仅具名复核批准后才可处理这些新增文件，不能整删linked或其主仓。
- 取消或受阻只关闭本次自建会话，保留源文件和证据。Owner信任记录留在既有隔离home，不复制到日常配置或擅自撤销。

推荐一次批准上述**O4具名执行范围**。此批准允许助手打开终端，并在Owner真正完成信任后继续步骤2–3；不代替Owner亲自信任，也不是未来所有工具操作批准。无额外模型任务、业务连接、L6、Git发布、P5/P6或旧资产清理。
