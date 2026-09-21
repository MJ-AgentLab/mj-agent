# R2D 修复后实际CI补验方案（待单独批准）

正式两文件修复已落地，主副本受控单测11项与22子测试、原生配置检查和lint通过。原实际run35485491970仍保留，但绑定旧守卫/测试，不能覆盖当前两文件增量。

- 平台：现有workflow的GitHub `ubuntu-latest`；不新增平台或改变gate。
- 私有仓库：`ranzuozhou/mj-agent-p4-acceptance-20260920`。
- 现有分支：`maintain/p4-acceptance-20260920`；已在本地核对HEAD `5bc6353f90e164ee22edee341d4f6b794b6aaa91`、工作区干净。远端须执行前重新只读核实，不假设尚未变化。
- 工作流：`.github/workflows/ci.yml`，现有`push: maintain/*`自动触发；权限`contents: read`。不新增workflow_dispatch、不创建分支/PR。
- 唯一发布工作区：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish`。正式原树和其他副本不暂存/提交/推送。
- 唯一更换文件：`scripts/sdd/codex_hook_guard.py`与`tests/unit/test_native_migration_guards.py`，具体差异为R2C-guard-fix-proposed.diff和R2C-tests-proposed.diff。前后SHA在R2C-review-binding.json。

已准备R2D-ci-proposed-binding.json：817交付+此前已批准的两个公共词表，共819条目标blob/checkout身份；815项当前交付按原换行映射逐项吻合，两项使用已应用新字节，词表不变。发布前核对全部819、源当前817及旧提交HEAD，禁止顺带发布其他文件。提交后记录commit/tree、两文件diff和全部blob映射；不以原仓HEAD代替交付绑定。

建议获准后执行：仅在上述ci publish同步两文件；确认暂存范围精确等于它们，再使用正常git命令：

```powershell
git -C 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish' add -- scripts/sdd/codex_hook_guard.py tests/unit/test_native_migration_guards.py
git -C 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish' commit -m 'fix: recognize Codex apply_patch command payload'
git -C 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish' push origin HEAD:refs/heads/maintain/p4-acceptance-20260920
```

禁止force或改权限解决拒绝。若HEAD/文件身份变动或正常操作拒绝，停下对应动作，不改命令/工具绕过。此次没有执行上述操作。

网络沿用已审阅GitHub及现有workflow公开依赖源；不新增基础镜像、项目MCP、业务服务、个人凭据或repository secrets。Actions正常临时令牌权限保持contents:read，不读取令牌内容。既有锁文件/检查器/离线runner与外部依赖跳过规则保持。

最小新增授权：仅该私有验收仓/现有分支的一次两文件本地测试提交、正常push及其自动CI运行，随后只读取结果和日志。证据保存到本仓evidence/codex-only-migration/p4-protection-remainder，记录run URL/id/attempt/head、每步结果和日志摘要，原失败/旧成功不覆盖。无需原仓发布、PR、权限调整或秘密。

恢复：本地源两文件原工作字节在`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration\.mj-agent-local\p4-topology-owner-console\R2C-source-before.zip`；旧私有验收提交`5bc6353f90e164ee22edee341d4f6b794b6aaa91`保留。不自动撤回远端历史或force推送；若需远端恢复须具名普通revert另批。CI完成也不自动解除R1规则独立拒绝缺口、不进入P5/P6。
