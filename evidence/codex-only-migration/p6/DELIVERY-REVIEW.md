# P6 具名交付审阅包

当前可审阅结果已准备，尚未获准执行原仓版本动作。P0–P5技术验收在批准范围内保留；P6最终消费者闭合待一行受保护政策修订。外部服务L6未验证。

## 身份与范围

- 原工作树：`D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration`。
- Git目录：`D:/workspace/10-software-project/projects/mj-agent/.bare/worktrees/codex-dev-mode-migration`；common-dir为同项目`.bare`。
- 分支：`maintain/codex-dev-mode-migration`；HEAD及实际两端develop均为 `20e2f24c352cf640d9dd33234b128ca897804b99`。
- 原仓暂存为空，索引SHA256 `b568c93beaebfec11f59da8bff0b39ef214dc066828c29d4f291f9ca35ca1382`。
- 逐文件集合：[file-inventory.csv](file-inventory.csv)。仅DELIVER行是拟提交集合；其他行逐项说明保留/排除，清单不是暂存授权。当前490路径：G1 255、G2 23、G3 212，包含97项既有删除。43项必要正式新文件全部纳入。
- 证据选择为具名必要证据及累计报告Markdown引用闭合，共210个证据路径；不是整个证据目录。未选的旧结果/候选继续保留本地。嵌入绝对路径及ZIP的历史恢复引用仍需要本机材料，不声称整个历史包可在Git clone后独立重放。

## 拟提交组与恢复

准确路径见 [commit-groups.json](commit-groups.json)，各组只在最终完整集合验证后依次提交，完成前三组前不推送中间状态。

| 组 | 提交信息 | 目的 | 恢复来源 |
|---|---|---|---|
| G1 | `infra: migrate development assets and retire legacy clients` | 原生技能/config/guard、直接契约/CI/模板/测试、准确81+16删除成组交付 | P0–P4公共备份+后续修复；legacy81准确ZIP；P6普通技能/模板before包 |
| G2 | `docs: document native Codex development and recovery` | 指南、根说明、CHANGELOG及必要索引 | P5六文件ZIP、P6before/additional-before ZIP |
| G3 | `docs: record migration acceptance and delivery evidence` | 计划、累计报告、资产表及明确证据 | P6before.zip保留旧报告/表；新增文件不清理；历史证据保持 |

保留当前Git作者配置；拟提交必须记录实际Codex贡献，不填虚构模型/邮箱trailer。提交后逐组核验树内容、暂存集合及SHA。受控验证前原仓最终文件列表需与本清单匹配；政策候选获批后的唯一预期增量须重新绑定该文件SHA。

## 新受保护增量

仅申请修改 `policies/ci-gates.md` §4季度审计一行，见[准确补丁](policy-proposed.diff)与[身份/影响/恢复](policy-review.json)。旧审计对象 `permissions.deny/ask`、`enabledPlugins` 改为当前原生config/hooks/rules边界、MCP传名漂移和实际hook证据；不改检查器、规则、权限、trust、契约或CI门禁。当前没有应用，旧§55批准不覆盖本行。

批准后应用前再次验证当前SHA；应用后检查准确单行diff、frontmatter、链接及未变保护文件摘要，更新AC-07/U07与最终清单。若发生技术拒绝，记录BLOCKED_EXECUTION_ROUTE并停止相关动作，不换工具/参数/编码/权限绕过。

## 远端与发布步骤（尚未执行）

只读证据见 [remote-observation.json](remote-observation.json)。两端迁移分支尚不存在，没有同分支PR或CI。GitHub传统保护接口404不覆盖有效ruleset：实际要求ci、strict同步、1审批、最后推送审批和线程解决；仅merge方式。

1. 上述政策单行批准并验证闭合后，复核原根、HEAD、空暂存、两端develop及目标分支新鲜状态；如目标变化则报告具体差异，不擅自reset、rebase或合并。
2. 仅按G1/G2/G3明确路径暂存、核验后提交；不用`git add .`、`-A`、证据目录或CSV原资产行批量暂存。所有拟交付修改/新文件/删除必须有对应组。
3. Gitee先推：`git push -u gitee refs/heads/maintain/codex-dev-mode-migration:refs/heads/maintain/codex-dev-mode-migration`。
4. GitHub后推：`git push -u origin refs/heads/maintain/codex-dev-mode-migration:refs/heads/maintain/codex-dev-mode-migration`。两端分别核对收到的SHA；不force-push。Gitee目标为 `https://gitee.com/ranzuozhou/mj-agent.git`；origin为 `https://github.com/MJ-AgentLab/mj-agent`。
5. 在GitHub创建PR：标题 `infra: migrate to native Codex-only development`；显式 `--repo MJ-AgentLab/mj-agent --base develop --head maintain/codex-dev-mode-migration`，正文以[PR-BODY.md](PR-BODY.md)作为`--body-file`。应用政策候选后先更新正文的待批准状态，不留虚假完成项。
6. origin的maintain分支push及目标develop的PR事件均匹配现有workflow，会触发Actions；不另行workflow_dispatch、重跑旧私有CI或发布验收仓。读取新run/jobs与review，把结果绑定准确head/merge-test SHA。失败/受阻/未观察分开记录，不以旧35564875219绿灯替代。
7. CI/review观察结束后更新累计报告并停止；人工merge、部署、issue关闭、分支/worktree或备份清理均不执行。

待交付材料不属于运行秘密，未选的候选/历史文件留在原树会使`git status`仍有未跟踪项；不为追求空status而清空/忽略它们。应核对“获准交付集合已全部提交”和“剩余仅清单排除项”，不把残留候选混入发布。

## 一次性待批准动作

请Owner对以下具名集合决定：政策单行应用及对应复验；原仓上述490路径在政策增量闭合后按三组暂存/commit；先Gitee后GitHub推送上述同名分支；创建指定develop-base PR；允许这些push/PR事件产生的现有CI并读取其结果及review状态。恢复与身份范围以本包为准。

这不是对merge、force-push、部署、真实凭据、L6、个人信任或额外清理的申请。之所以仍需批准，是本次P6提示词第五节明确保留原仓发布授权，根AGENTS第4条及Git commit/push/PR技能也要求具名Owner决定；政策行另受`policies/ai-agent.md` §5元规则保护。历史私有验收发布和P5删除批准均不覆盖本次动作。


## 批准后执行更新

Owner已对上述完整具名包回复“批准”。政策单行已按proposed SHA准确应用并通过frontmatter、链接与diff检查；正文无额外变化。原有待批准叙述保留为审阅时点，当前开始G1/G2/G3版本执行。原始包的精确备份为`.mj-agent-local/p6-publication/approved-package-before.zip`；实际提交、双推、PR/CI结果后续按观察追加，不预填成功。


## 实际版本停点

G1准确255路径已获准暂存，暂存检查通过；`git commit`尚未启动即被执行策略拒绝：`approval required by policy, but AskForApproval is set to Never`。当前为BLOCKED_EXECUTION_ROUTE；未换工具/参数/编码/权限重试。HEAD仍20e2f24c，新增提交0。G2/G3未暂存；双推、PR、CI、review、merge均未执行。

暂存使原先未跟踪的offline安全测试进入diff检查，暴露两条末尾空行；已在同一批准G1文件内做EOF-only最小修正、准确备份并重新暂存，AST/全部断言不变，git diff --cached --check现exit0。测试没有重跑，原P5行为证据按AST不变范围保留。当前索引与255路径清单见final-check.json的publication_execution。不得恢复旧空索引或重做已完成阶段；保持Owner本次批准有效，后续先核对可执行路线和现场，再从提交停点继续。


## Owner执行后的当前状态

G1已由Owner提交并独立验证：`e5f99c87a50ad47856a41f40c2acccf75a5534da`，准确255路径，原父提交20e2f24c。G2准确23文件已暂存且cached diff检查exit0，等待Owner提交；G3尚未暂存。原有批准继续有效。之前“零提交”的记录仅对应拒绝时点，最新依据为累计报告§64及final-check.json的owner_g1_observation。尚未push、创建PR或观察最终CI/review；三组完成前不推送。Codex执行审批路线未变，不重试被拒commit。


## Owner完成G2后的状态

G1/G2均已提交并逐路径/工作字节核验，最新HEAD为`1eb9257f15ee250b732f5db8a7f0b4266c0d2401`。G3维持原批准212路径，准备暂存及人工提交，实际检查见累计报告§65。三组完成前不推送；双推、PR、最终CI/review/merge未执行或未观察。Codex执行审批路线不变，既有批准继续有效。


G3现已准确暂存212路径；完整cached diff检查exit2，2161条均来自20份字节未变的已批准历史补丁/Markdown。保留原文及失败结果，不改门禁、不声称全绿；逐文件诊断见final-check.json的owner_g2_observation.G3与累计§65。等待Owner人工提交G3，完成后再核对最终提交与双远端发布步骤。
