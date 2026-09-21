# R2C 精确兼容修复与一次副本验证（待批准）

R2B实际确认Codex CLI0.147.0向hook传递`tool_input.command`，补丁内容精确等于已审阅合成请求。现有dict分支只读file_path/path，导致UNKNOWN。R2B已按SHA恢复；这属于计划§2.4的迁移接口缺陷，不是继承业务问题。

修复仅在apply_patch的dict包含command时识别精确单字段字符串，再沿用原路径解析；混合字段及非字符串仍UNKNOWN。没有增加ALLOW分支、改变保护路径、放宽权限或保留观测日志。见[R2C-guard-fix-proposed.diff](R2C-guard-fix-proposed.diff)。已准备[R2C-tests-proposed.diff](R2C-tests-proposed.diff)，保留所有旧断言，补充保护/秘密/普通路径、混合字段、异常类型及Move目的地断言，尚未应用正式测试。

候选纯组件23例及一次合成stdin不回显检查已实际通过；基线对command包装的保护删除返回UNKNOWN，候选返回OWNER_APPROVAL_REQUIRED。此结果不是受控pytest或宿主通过，两者仍单列NOT_TESTED。

本次建议批准范围只有**一个临时目标**：`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance\scripts\sdd\codex_hook_guard.py`。前SHA `422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608`，候选SHA `033d28a9b9918f8a4576376d61c1892e782a6f24cbb764b64781339fb905bfad`。执行一次原样删除不存在文件`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance\.codex\P4_CANARY_DELETE_6a41.txt`，不创建目标。保护失效时也仅可遇文件不存在错误，此错误不算保护通过。预期真实PreToolUse返回`OWNER_APPROVAL_REQUIRED: protected edit; human decision required`，首次block即停止，无工具改写或重试。

沿用CLI0.147.0 / gpt-5.6-sol / 官方OpenAI模型连接、strict-config、8MCP关闭、readOnly、networkAccess=false、180秒和正常取证驱动。hook定义不变，不代信任；如宿主要求新信任或路线拒绝则停止。仅将驱动冻结身份替换为候选，移除已不适用的观测日志不存在断言并调整案例名/说明，全部差异附R2C-host-proposed.diff。

批准后助手执行以下具名步骤（Owner无需编脚本或代填审批）：

```powershell
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2C-apply-restore.ps1' -Action Apply
& 'C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2C-host-proposed.py' canary --location root --model gpt-5.6-sol --canary-id R2C_PROTECTED_CLASSIFICATION
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2C-apply-restore.ps1' -Action Restore
```

Restore沿用刚刚实际走通的PowerShell正常路线，恢复`R2-guard-before.py`，公共备份`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\.mj-agent-local\p4-topology-owner-console\R2-guard-before.zip`，SHA `a74e6a25f9e4f4a0e049a921fc78d5bd6d6967666cd6c54547bbcaa517ee3a9c`。任何未知身份不覆盖。即使canary拒绝也执行已批准的精确恢复，恢复受拒绝则报告，不换工具。前后复核原树817、主副本816+具名守卫增量，恢复后817，原/副本索引和缺失目标；保存真实payload、hook结果和停止事件。

本次批准不包括正式源与测试应用。正式两文件候选及恢复包已备齐：`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\.mj-agent-local\p4-topology-owner-console\R2C-source-before.zip`（SHA `71d3ee87d0afa400dfda4dc6af76ccb110311d9afb8da75ada0be8e3ec52dfeb`）。副本验证成功后，正式应用沿用Owner具体差异审阅和可执行路线；正式应用将改变817中的两项身份，必须更新交付绑定及受影响回归。现有实际CI只证明原绑定，不能冒充新守卫版本CI通过；本轮不触发远端CI，不提交发布。不能把副本试验成功标为正式修复完成。

推荐A：批准上述一个副本守卫Apply→一次分类验证→Restore。B：保留候选和当前恢复状态，暂不执行。此项需具体批准，依据根AGENTS及policies/ai-agent.md§4对原生守卫的保护面要求；上次R2B仅批准观测，明确不含分类修复。

R1独立rule证据仍受阻，不关hook来制造规则独立结果。P4未验收，P5 BLOCKED_PREREQUISITE；不执行P5/P6或旧资产清理。
