# R2E 远端HEAD只读复查（待批准）

既有私有仓两文件提交、push、CI授权已取得并保持。本次gh repo view私有性/name检查通过；随后原样ref API读取exit1。首个helper未保存stderr，因此不能把未知原因称为网络、认证或服务拒绝。没有暂存、提交、push或CI触发。

唯一复查命令：

```powershell
gh api repos/ranzuozhou/mj-agent-p4-acceptance-20260920/git/ref/heads/maintain/p4-acceptance-20260920
```

仍使用绑定的同一gh.exe、正常既有认证和同一接口，最多30秒、一次请求；不切换工具、编码、端点、权限、凭据或网络配置。stderr先保留于进程内，仅将HTTP状态、固定错误类别及有界脱敏信息存入证据，任何可能凭据值不打印、不写日志；不读取认证配置。成功时验证object.sha必须等于5bc6353f90e164ee22edee341d4f6b794b6aaa91，否则停止，不同步/覆盖。

成功后继续已经明确获准的两文件私有验收发布；失败或超时后停止，不自动再试。此前R2D方案中origin为示例别名，本地已只读核实实际唯一指向同一批准URL的remote是acceptance；后续使用该已有别名，不新增或改remote。maintain分支提交type按既有规范用infra(scripts)，文件集合与授权不变。

本地ci publish仍为旧HEAD且干净，819项blob和工作字节按既有换行映射通过；原/主当前817和原索引保持。已有成功与失败证据均保留。R1独立rule仍缺，本次复查不解决它，不进入P5/P6。
