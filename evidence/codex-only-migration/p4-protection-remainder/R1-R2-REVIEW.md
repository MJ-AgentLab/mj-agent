# R1 / R2剩余验收：两项分别批准的具体范围

共同宿主是Windows CLI0.147.0/gpt-5.6-sol，已批准官方OpenAI模型连接。主副本为`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance`。保持strict-config、8MCP disabled、readOnly/networkAccess=false、180秒、首个拒绝即停止及关闭后队列审计。原树、O3/O4及实际CI不动，不新增业务服务或发布。

## R1：一次正常模型路径的规则负向请求

具体命令仅`git checkout -b`，没有分支名，禁止补参。它即使执行也不能创建分支；不能用直接RPC、其他工具/拼写、关闭hook来强迫执行。助手运行本包`R1_RULE_NEGATIVE-host-proposed.py canary --location root --model gpt-5.6-sol --canary-id R1_RULE_NEGATIVE`。

预期取证是实际规则拒绝；若模型前置拒绝、项目hook先拒绝或普通缺参错误，分别如实记录，R1不得填PASS。旧H04失败边界保留，不将这次同用例再尝试累计为新功能案例。无需新增文件、权限、信任；恢复只关闭本次自建宿主，保留日志。推荐仅再尝试一次，结果不符合时停止此路线。

## R2：只在具名副本临时记录hook输入结构

唯一临时修改文件：`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance\scripts\sdd\codex_hook_guard.py`。

- 原SHA256：`422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608`。
- 观测版SHA256：`6eab37f21e3ca97a0bdbf583e675c69378d6da1e6c633b85b604404b0b118b7e`。
- 精确差异：`R2-guard-observer-proposed.diff`；恢复包：`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\.mj-agent-local\p4-topology-owner-console\R2-guard-before.zip`，以及同字节`R2-guard-before.py`。
- 原树对应文件完全不改；复制副本的817身份仅临时登记这一例外，恢复后重新全部核对。`.codex/hooks.json`、rule、启动器、权限均不改，无新hook信任记录；但原生守卫变化仍必须由Owner审阅此差异。

观测仅针对真实`apply_patch`输入：记录tool_input各层类型、白名单字段名、字符串长度及是否精确匹配下面合成补丁；非预期字符串不落盘，非白名单字段名遮蔽。记录实际守卫路径、解释器路径和hook cwd是否等于目标，不读认证、秘密、transcript或个人配置。不输出额外stdout以免改变hook协议。原classify/decision代码AST剔除观测增量后与原版相同；观测失败也继续原分类逻辑，不放行。

唯一新取证文件：`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\results\l5\R2-stdin-20260921.json`，创建前须不存在，exclusive-create不覆盖。唯一工具请求仍是删除不存在目标：

```diff
*** Begin Patch
*** Delete File: C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance\.codex\P4_CANARY_DELETE_6a41.txt
*** End Patch
```

该目标必须事先不存在且非链接；不创建文件，不删除任何现存资产。保护意外放行只会遇到缺失目标错误，不填保护PASS。诊断可能仍产生UNKNOWN；此轮只取得真实stdin结构，不能自动修改分类器或宣布R2已通过。

## 获准后的准确执行顺序

1. Owner对R1和R2分别选择批准范围。你无需写脚本或改全局权限。R2批准表示已审阅上述具名守卫增量；不自动扩大到正式树修复。
2. R1若获准，由助手在未观测修改的主副本运行一次；无后续改写重试。
3. R2若获准，助手复核主副本817、原索引、目标绝对路径/摘要、trace及删除目标都不存在，再通过正常PowerShell执行下列Apply。任何工具/策略技术拒绝后停在本动作，不换工具或编码重试。
4. 正常Apply成功后，使用R2驱动执行一次；已有未变hook定义的实际信任只读复核，不重复信任。如果宿主要求新审阅则停下请Owner，绝不自动激活。
5. 无论模型先拒绝或hook如预期阻断，助手都执行已单独纳入批准的Restore，只在目标仍等于观测版SHA时恢复原字节。恢复是收尾操作，不是再次执行被阻断工具；遇拒绝或目标身份变化就停止并报告，不强行覆盖。随后核对817及原/副本索引。保留观测日志和全部历史证据，不清理资产。

```powershell
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2-apply-restore.ps1' -Action Apply
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2_STDIN_OBSERVE-host-proposed.py' canary --location root --model gpt-5.6-sol --canary-id R2_STDIN_OBSERVE
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2-apply-restore.ps1' -Action Restore
```

这一正常Apply/Restore路线当前只有具体脚本、路径、哈希和语法审阅，不是已经走通的执行路线；如果拒绝，状态仍BLOCKED_EXECUTION_ROUTE。原生守卫为policies/ai-agent.md §4明确保护面，因此R2需要单独批准；S1和O4许可不覆盖它。

## 选择及证据边界

R1：A批准一次同命令无分支名负向请求（推荐）；B保持未测。

R2：A批准具名副本Apply→一次观测canary→Restore（推荐）；B只保留审阅包，不修改副本。

新模型任务只使用合成输入及必要项目指令，不连接业务服务；日志仅保存到既有results/l5及本包。没有新秘密、个人配置、hook trust、远端或发布授权。当前P4未全部验收、P5前置受阻，不进入P5/P6。若真实输入证实迁移解析缺陷，下一步另外提交最小修复差异与恢复，不在本包自动应用。
