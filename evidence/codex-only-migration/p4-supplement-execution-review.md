# P4 补验执行路线与 G19 修复审阅

状态：P4 已重新进入；G19 实际失败，L5/平台缺口仍未闭合；Windows完整交付拓扑已取得实际组件证据。此文件不批准提交、信任、hooks、外部服务或清理。

## 已完成

188 项正式组、817 项交付源/副本、387 项清理身份重新匹配。20 条新增本地检查中19条exit0，G19 exit1（22P/0W/2F）。exit0中的无合同、条件未触发、skeleton和WARN均保留原语义，不称20项测试全部通过。
CLI 0.147.0离线导出361份协议schema；确认 skills/list、hooks/list、hook运行通知存在。hooks/list定义包含sourcePath/currentHash/enabled/trustStatus，但本轮没有实际调用或取得已加载信任状态。导出方法名中未发现hook simulate/test/dry-run接口；不推定不存在任何内部能力，也不试发真实危险命令。

## 一、两行受保护契约修复（已批准，待 Owner 人工应用）

目标：`capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature`。
仅恢复两个场景原有的 `@CTR-mcp-server` 标签；契约ID、trace、场景正文、测试断言及门禁不改。
差异：`p4-supplement-g19-proposed.diff`；恢复差异：`p4-supplement-g19-recovery.diff`。
原SHA256：`586fe2a078748f9fe362008bcfaac47b60fd44afae0917d946e942b49e7da1bf`；预期SHA256：`da0ecc2a8a49c46548386cf4bf31cfc8fbec09dd5610dfeef492d19d486928bd`。
准确恢复ZIP：`.mj-agent-local\p4-supplement\g19-before.zip`，SHA256 `4c75bd754cb6d4271d60c362a7e2f81620b02bb5b62f52ae030de93579787e69`。
只读 `git apply --check` 通过，候选两场景的REQ/CTR绑定均可解析；正式G19仍失败。

依据 policies/ai-agent.md §4 declared-contract-change，新的两行差异须 Owner 拍板，不能把A1–A6旧冻结批准当作本次批准。
沿用 P3 已验证路线：Owner 审阅后，在具名迁移根目录自己的终端执行：

```powershell
git apply --check -- 'evidence/codex-only-migration/p4-supplement-g19-proposed.diff'
git apply -- 'evidence/codex-only-migration/p4-supplement-g19-proposed.diff'
```

Owner已答复“批准两行修复，我人工应用后通知”；当前正式文件仍为原SHA，本轮未执行第二条。应用后Codex核对目标SHA，登记817清单中单项增量，再同步副本与其测试索引，复跑G19、trace和MCP BDD。原树不暂存。

## 二、完整交付拓扑（具名例外已批准并执行）

Owner明确允许“该一次性测试提交与两个拓扑副本”。在既有native acceptance副本建立唯一测试提交`e25cda790f881e7986122e94a8597c7acf3d1bbc`，tree为`cf67762486245325c178dc53226ffc61357b84d9`；内容817文件，保留已核验的两项P4修复，G19新差异尚未应用。没有停用hook或修改权限，正常操作未被技术拒绝。
同临时父目录的`topology clone`使用`git clone --no-hardlinks --revision=<SHA>`建立detached checkout；Git自动产生的唯一origin仅指向本地副本，立即删除，最终无远端。`topology linked`使用`git worktree add --detach`，只登记于一次性副本自己的Git元数据。原树索引/HEAD/分支/worktree登记未动。
两处均有817文件、同一Git树；只有GLOSSARY工作区字节因Git正常checkout产生LF/CRLF差异，已逐项登记并确认除此之外完全相同。没有复制缓存或原仓秘密/旧客户端。
两种拓扑的根与tests/unit子目录均通过原生技能/资源/入口/消费者/config检查，缺凭据MCP启动以exit3在npx前停止，直接guard的允许/保护拒绝/异常拒绝组件观测符合预期。受控runner的5个安全/边界相关单元文件分别106 passed、19 subtests passed。此处是Windows组件/离线程序证据，不是宿主hooks激活、Linux或实际CI。
具体命令和逐文件SHA见`p4-supplement-topology.json`。只验证已授权快照，不把尚未人工应用的G19差异混入提交；未来增量须独立绑定。没有删除两个副本或恢复包。

## 三、Linux 与实际 CI（环境缺失）

只读WSL枚举仅docker-desktop；Docker context为desktop-linux，但本地Linux引擎管道不存在，image ls exit1。没有启动Desktop/daemon/容器、切换context、下载镜像或安装系统。
实际CI工作流需要checkout/setup/依赖安装及平台运行，当前没有外部连接/发布授权与可用结果。p4-supplement-ci-matrix.json逐步保留NOT_TESTED。本轮Windows checker执行不能替代ubuntu-latest或GitHub Actions结果。
需提供已就绪Linux离线环境或绑定当前交付身份的运行记录；不得把通用“继续”理解为推送、workflow dispatch、开放服务或安装依赖。

## 四、L5 实际宿主（路线缺失）

工程师须独立审阅项目/hook信任，并提供无项目MCP/业务服务连接的宿主执行路线；模型canary与项目服务边界需要明确。正式配置包含8个项目MCP启动定义，不能靠提示词阻止启动。
本轮没有改个人配置、隔离副本的信任/权限、激活hooks或启动模型。宿主路线仍BLOCKED_EXECUTION_ROUTE，行为NOT_TESTED/UNMET_DEPENDENCY。U04的P3人工应用路线继续MANUAL_ROUTE_EXECUTED_VERIFIED。
清理仍BLOCKED_PREREQUISITE；上述审阅材料不构成P5删除授权。
