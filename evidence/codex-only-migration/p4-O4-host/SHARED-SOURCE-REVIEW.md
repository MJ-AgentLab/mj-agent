# O4 linked：共享来源的具名修订（待Owner批准）

## 已有证据与未决原因

CLI0.147.0的实际hooks/list和Owner截图均显示：linked根、src/mj_agent、tests使用native acceptance/.codex/hooks.json；Git common-dir恰为native acceptance/.git。37个项目技能仍来自linked自身。三处（原树、linked、此共享主副本）的3个.codex文件及2个守卫脚本摘要均一致，无额外.codex文件。

本机安装包未提供实现源码。已读取[官方高级配置](https://learn.chatgpt.com/docs/config-file/config-advanced?translationFallback=zh-Hans)，它说明hook随配置层加载，但没有明确描述0.147.0的linked共享来源算法。因此不把关联推断写成根因已证实，也不以文档代替实际验收。本次建议在具名共享来源上继续取得行为证据；将来linked与共享主副本定义分叉时的行为仍未测试。

## 唯一新增批准范围

将O4原来只接受linked/.codex/hooks.json的取证预期，改为仅接受以下实际来源，并新增共享Git关系、5文件摘要、唯一hook/currentHash和linked指令来源检查：

`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/native acceptance/.codex/hooks.json`

实际工作目录保持：

`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology linked`

具体差异见[host-O4-shared-source-proposed.diff](host-O4-shared-source-proposed.diff)，摘要见[shared-source-review-binding.json](shared-source-review-binding.json)。这是普通取证驱动的新候选文件；旧驱动保留。原生hook/rule、配置、Git连接、权限和正式资产均不修改；不接受任意父目录或任意同名hook。

## Owner准确操作

1. 批准本修订后，仍在已打开的“topology linked”CLI详情页审阅当前单项。核对Source为上述native acceptance绝对来源，事件PreToolUse、matcher `Bash|shell|exec_command|apply_patch|Edit|Write`、timeout30秒。
2. 完整解码见[hook-decoded.ps1.txt](../p4-l5-route-v2/hook-decoded.ps1.txt)。其命令用git取得运行cwd的仓库根，再调用该根的scripts/sdd/run_codex_hook.ps1；不能只凭这段静态代码断言宿主实际hook cwd已验证。
3. Owner亲自按`t`信任这个详情页的单项；不是在总览选择信任全部。确认`Trust: Trusted`及`[x] Hook 1`，按Esc返回，确认Installed1/Active1。若路径、条目、定义有变化则停止。聊天批准不代替这一步。
4. 反馈实际完成状态。助手只读复核当前信任与绑定后继续，无需再次申请已批准的同一环境/模型范围。没有单独项目级信任UI记录时，不补造该记录。

## 助手后续执行与成功条件

批准并实际信任完成后：仅在linked/.venv使用已绑定CPython3.13.5执行`-B -m venv --without-pip`，不联网、不装包，记录每个生成文件及恢复前态。预期缺失目标若已出现则停止，不覆盖。

```powershell
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-O4-host/host-O4-shared-source-proposed.py' canary --location root --model gpt-5.6-sol --canary-id O4_ROOT_STATUS
```

只执行一次真实`git status --short`；固定官方OpenAI模型提供者、8MCP关闭、strict-config、readOnly/networkAccess=false和180秒。任何hook block、非预期审批或来源变化即停，不换工具重试。需保存真实tool payload/cwd、hook事件及来源、exit、turn结尾和前后文件/索引身份。工具cwd须为linked；指令来源须为linked/AGENTS.md；37技能来源仍为linked。hook来源只接受上面的共享主副本。缺失事件、模型口头拒绝或不正确cwd均不记PASS；hook内部进程cwd/解释器若没有日志，单独明确未直接取证，不推定。

运行结果目录仍位于`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/results/l5/`；没有业务模型任务、业务MCP连接、CI重跑或发布。

## 恢复与选择

候选未执行，无需恢复正式文件；原驱动及原批准包保持。只有未来执行后的linked/.venv具名清单属于新增目标，原态不存在；本轮不删除。Owner信任留在既有隔离home，不读取或复制其认证/个人配置，也不代撤销信任。原树及共享主副本只读，Git基线和P0–P4未提交成果备份继续分开。

- A（推荐）：批准这个共享来源及候选驱动修订；Owner亲自信任该具名单项后，助手执行已限定的环境和一次canary。
- B：保持O4受阻，不信任新来源；保留现有证据，本轮停止该项。

P4仍未验收，P5受前置阻塞；本方案不关闭R1/R2或真实首阻断停止分支缺口，不进入P5/P6。
