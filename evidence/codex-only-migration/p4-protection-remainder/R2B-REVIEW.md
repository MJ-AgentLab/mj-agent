# R2B：仅补记精确合成补丁的字段名（待批准）

R2已按批准正常Apply、实际观测一次、Restore成功。真实tool_input是单字段dict，其163字符字符串精确等于具名删除补丁；原守卫拒绝为UNKNOWN/no recognized edit target。但字段名不在观测白名单，被遮蔽为<other>。不能猜测字段名修改分类器，R2尚未验收。

本次唯一观测增量：当某字段的值**精确匹配原已审阅合成补丁**且字段名是最长64字符的ASCII标识符时，允许保存这个字段名；非预期值、其他字段名仍遮蔽。增量见[R2B-observer-increment.diff](R2B-observer-increment.diff)。新输出文件`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\results\l5\R2-stdin-key-20260921.json`，不覆盖旧证据。原分类/阻断代码依旧不改。

唯一临时修改目标：`C:\Users\Admin\AppData\Local\Temp\mj-agent-p4-host-ci-20260920\l5 native acceptance\scripts\sdd\codex_hook_guard.py`。当前已恢复SHA `422c6e54249312714a2f64e1f51ace6575135470a1355b5d5e3f098ddf051608`；新观测SHA `c8c9a7e77f8366a772ca2a6095af4ccc18b011f86414424194bb7632e115cd03`。原树、其他副本、.codex/hooks.json、规则、启动器、权限及信任不改。原hook定义摘要不变，无需重新信任；若宿主出现新审阅要求，则实际停止而非代信任。

仍只请求一次删除不存在的`.codex/P4_CANARY_DELETE_6a41.txt`，不创建任何目标；即使放行也只有缺失文件错误。CLI0.147.0/gpt-5.6-sol、官方OpenAI连接、8MCP关闭、strict-config、只读/禁网和180秒保持，首次拒绝即停，无改写重试。

批准后助手执行：

```powershell
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2B-apply-restore.ps1' -Action Apply
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2B_STDIN_KEY-host-proposed.py' canary --location root --model gpt-5.6-sol --canary-id R2B_STDIN_KEY
& 'D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\evidence\codex-only-migration\p4-protection-remainder\R2B-apply-restore.ps1' -Action Restore
```

这沿用刚刚实际走通的正常PowerShell路径，不切换工具/编码/权限。Apply和Restore均锁定目标及双向SHA，未知身份不覆盖。恢复使用已保留原字节`R2-guard-before.py`及`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\.mj-agent-local\p4-topology-owner-console\R2-guard-before.zip`。预期拒绝后仍只执行已批准恢复，不再次发起工具请求；恢复遇拒绝则停止报告。原/副本817和索引前后复核；取证日志保留，不清理旧资产。

推荐A：批准R2B精确观测增量、一次canary及恢复。B：保持已恢复状态，不再观测。需要具体批准，因为这是上次已执行完毕的保护面观测之后新增的一行字段名输出范围和新身份，不自动扩展旧SHA批准。

当前只完成候选语法及纯结构检查；不是再次宿主执行。即使取得字段名，也仅完成根因证据；正式兼容修复、回归测试和再次真实分类验收仍另列差异，不把新观察直接当PASS。R1实际G1 hook拒绝证据保留，原生rule独立证据仍缺，P4未验收、P5受阻，不进入P5/P6。
