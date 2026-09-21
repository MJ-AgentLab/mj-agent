# 六文件消费者修复：具名实际 CI 审阅

正式修复与恢复事件见 manifest.json、proposed.diff、incident.json、recovery-result.json。源/主副本当前817身份一致。短路径受控pytest39项通过；原105条断言未动，运行时代码AST未动。无重复宿主canary。

## 目标、文件和触发

- GitHub私有仓：`ranzuozhou/mj-agent-p4-acceptance-20260920`。
- 已有分支：`maintain/p4-acceptance-20260920`。
- 唯一发布副本：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish`。
- 本地基线：`208dfa915d9fc465b64dd7131959367df0128c26`，只读检查干净。远端在获批执行前再核对，若变化停止。
- 现有remote `acceptance` 已核对为该仓HTTPS URL；不改remote或创建新分支。
- workflow：`.github/workflows/ci.yml`；现有 `push: maintain/*` 自动触发；Ubuntu、`contents: read`及原离线测试策略保持。其他由既有push配置触发的只读检查照实记录，不改触发器或gate。
- 只提交下列6文件，具体前后差异/字节在 proposed.diff、manifest.json：
  - `tests/fixtures/development-agent/scenarios/S5/expected.yml`
  - `tests/fixtures/development-agent/scenarios/S5/request.md`
  - `tests/unit/test_sdd_development_agent.py`
  - `docs/INDEX.md`
  - `policies/ci-gates.md`
  - `src/mj_agent/env_drift.py`

CI-binding-proposed.json绑定当前817交付及原已批两个公共词表，共819blob；813blob不变，6blob为本次修复，Markdown的CRLF→LF转换显式记录。发布前核对全部暂存blob、变化集合及当前源SHA，不包含审阅包、日志、恢复包或原仓历史。

## 唯一发布路线（未执行）

获批后在上述副本同步6文件，核对字节；`git add -- <上述6个完整相对路径>`；确认暂存集合精确为6项，再正常提交：

```powershell
git -C 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish' -c user.name='Codex P4 acceptance' -c user.email='codex-p4@localhost' commit -m 'infra: replace remaining legacy development consumers'
git -C 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/ci publish' push acceptance HEAD:refs/heads/maintain/p4-acceptance-20260920
```

只在该私有验收副本提交/推送一次，随后读取实际run/head/attempt/步骤和日志。原仓不暂存、不提交/推送，不建PR、不合并、不做P5清理。若正常路线拒绝，停下，不force或换保护/工具绕过。非预期原仓提交已经按Owner批准恢复，本CI路线不会引用或推送该提交。

## 网络、权限、证据和恢复

网络限已审阅GitHub及现有workflow公共依赖源，不启项目MCP/业务服务，不增加secret，不读取登录令牌，不改个人权限/配置。旧CI35560658984继续作为上版证据；新run不能只用旧绿灯替代。

结果保存至本目录：精确commit/tree/819blob映射、远端ref、run URL/id/head/attempt、逐step结果、日志及SHA；失败与skip按实记录。原索引恢复后新摘要见recovery-result.json，执行前后再次核对。

恢复来源：六文件修改前准确工作字节在 `.mj-agent-local/p4-consumer-fix/before.zip`；CI副本修改前六文件在 `ci-before.zip`，此前提交208dfa…保留。不自动撤回远端或强推；若需远端撤销，另审阅具名revert。此授权不包括原仓发布或P6。

最小新增授权：本具名私有验收仓/已有分支的这6文件一次提交、push及自动CI，随后只读取证。此前两文件CI批准未覆盖本次6文件。
