---
type: plan
summary: 对齐mj-system的Codex项目配置结构并评估九个SSH历史入口
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: completed
track: engineering-workflow
---

# Codex 配置结构对齐与 SSH 评估

## 原意、基线与范围

原意正本为本旁聊Owner请求：“按照上述结构对齐，并评估为mj-agent配置以下mcp，让codex可以连接”，具名入口为cloud、runner-lan/runner-wan、test-lan/test-wan、prod-lan/prod-wan、dgx-lan/dgx-wan。此前Owner采纳的结构是项目配置主要保留MCP，审批/沙箱取实际宿主设置，退出项目hooks/rules自动加载及专属加载取证要求，保留数据、秘密、Git/Owner与平台边界。退出自动拦截不等于AGENTS或CI提供等价事前强制保护。

代码基线1022610eb4d0ada6352312e080965eeb8afe94ee；已完成608主题不重开。本任务无主要Issue；整体主PR已真实建立为 [#611](https://github.com/MJ-AgentLab/mj-agent/pull/611)，head=maintain/codex-config-alignment，base=develop，作者mj-agent-delivery-executor[bot]。原无编号检查点保存在d6bc62b。工作树为D:/workspace/10-software-project/projects/mj-agent/maintain/codex-config-alignment，分支maintain/codex-config-alignment。原实施阶段不写develop；Owner本轮“已合并，继续后续工作”后仅正常快进develop、安装已合入MCP的本地依赖，其他任务不写入。

实施仅本地配置/检查器/相应测试/当前政策技能契约文档。Owner于2026-10-29明确“执行B”：增加一个ssh-manager，全部9历史入口按既有账户接入，含cloud root及生产。原8项保持，加上SSH共9项MCP；仅凭据名称复用，不解密/复制秘密，不改个人配置。可做本地模拟MCP启动/握手，真实主机连接/远程命令不在本轮执行。旧ADR和验收记录不改成PASS。

## 可观察AC与验证

- AC1：当前项目config仅声明原8项与B决定的1项ssh-manager，共9项MCP；没有项目审批/沙箱覆盖，无个人配置写入。
- AC2：项目自动hooks/rules退出；旧软件诊断/测试资源有明确历史用途，默认配置检查不再要求宿主守卫加载取证。
- AC3：V11仍检查MCP用途/按名凭据与合法结构；错误、间接文件或禁入服务继续失败，不输出秘密。CI不靠跳过错误或默许白名单外服务通过；只增加Owner已决定的具名SSH。
- AC4：普通Git工作流、Owner接受、App发布与业务/秘密边界保持；无项目自动拦截的局限真实说明。
- AC5：当前政策、技能入口、消费者/合同与检查器一致；原历史拒绝/UNKNOWN保留；独立可信门禁等延期不被冒充完成。
- AC6：SSH为1个MCP、9入口、5类主机/5组变量；按Owner B选择配置全部入口/既有账户，明确通用远程执行和cloud root/生产权限影响，不读取凭据给模型。
- AC8：SSH启动自包含且依赖锁定，仅列出/单目标执行工具；未知服务/内联密码、缺凭据、未知或错误主机密钥、超时/取消/输出上限有离线负例。实际Codex发现、逐主机认证与命令结果单列未测。
- AC7：适用离线回归、文档、native与类型/格式检查有本轮真实结果；未测/依赖和独立核验状态分列。

## 授权、风险与停止

Owner已授权结构本地对齐、SSH评估及后续方案B的本地配置/依赖安装/准入同步和模拟验证。退出具名项目载体.codex/hooks.json与.codex/rules/mj-agent.rules属于已采纳结构；两者原Git字节由基线提交恢复，删除前核真实目标、跟踪/改动和重解析点，不清理目录或其他内容。最初仅本地准备；Owner随后明确“提交PR”，授权本主题在当前worktree暂存/提交、推送并向MJ-AgentLab/mj-agent的develop创建PR，不授权merge、账户/个人权限变更或真实主机连接。其后本会话Q1已授权本轮临时Workflows write并在发布后撤回；Q2明确“使用双推”，默认Gitee→GitHub，无Gitee延期例外。B允许的账户范围不等于远程动作授权。

旁聊禁止使用子Agent，故本地自检不冒称独立核验。立项时独立核验和Owner准确版本接受列为后续；本轮Q4已明确接受准确版本并将独立/宿主/真实认证等未完成项移出本轮完成条件，原未测不计PASS。实际技术拒绝只停受影响步骤并保留原错，不换工具或改配置绕过。

## 依赖、交付与恢复

先保留旧守卫的合成fixture，再以新配置正负例红绿验证；同步当前消费者，历史记录保持。SSH评估见 [评估报告](./[ASSESSMENT]_ssh_mcp_access.md)。MCP信任、服务连接和远程运行分开；新会话MCP加载需正常宿主验证。

恢复为基线Git文件与本分支实际diff，不涉及服务器、凭据或数据恢复。PR611已合入develop的db4a85d，Owner本轮Q4已接受配置/离线版本并明确延期其余未完成项；AC1–6和AC8有静态/离线证据，AC7本轮结果见本地报告。独立核验、真实宿主发现/认证仍未执行；Owner准确版本接受已在本轮Q4明确发生，主Plan依实际决定completed，不以文件存在、合并或机器通过推定接受。

## PR发布准备检查点（历史）

2026-10-29，Owner明确“提交PR”。远端develop以GitHub连接器回读为1022610eb4d0ada6352312e080965eeb8afe94ee，与当前基线相同；maintain/codex-config-alignment尚无远端分支/同分支PR。独立旁聊不派子Agent，自检/本地验证不认证独立审核。普通stage/commit/PR所需准备沿本次请求推进，merge及整体接受未授权。

既有App5284037、installation170545174的daily受控审计为EXECUTOR_VERIFIED，仅metadata read、contents/pull_requests write，单仓repository1172583390；短期token撤销CONFIRMED。候选包含ci.yml变更，当前无Workflows write，尚未尝试被预知不允许的推送；不会使用Owner/MCP身份替代或改权限绕过。准备候选提交和PR正文后，仅就本轮临时Workflows write及Gitee发布范围给Owner具体选项，旧任务授权不移用。

## 本轮发布与真实决定

2026-10-29，本会话Q1明确“授权本轮临时 Workflows write，发布后撤回核验（推荐）”，范围仅App5284037、installation170545174、MJ-AgentLab/mj-agent；Q2明确“使用双推”。初始候选d6bc62bde64f7db230766f31c3f0a2ea54f9a563使用正常Git不可见鉴权先推Gitee，并实时ls-remote读回同SHA；Git协议不返回实际账户ID，不额外认证账户身份。GitHub本人认证由Owner完成，本会话Q3明确完成；不采集或回传口令/验证码。

Agent经正常GitHub权限页仅启用本轮Workflows write并在现有单仓installation接受。受控bootstrap审计确认App/installation/token层仅metadata read、contents/pull_requests/workflows write、单仓repository1172583390，token撤销CONFIRMED。随后固定后台完成origin推送及PR611创建，两次token均CONFIRMED撤销；连接器回读PR611为OPEN、base develop、head d6bc62b、作者既有App，未merged。PR创建后经正常权限页撤回Workflows write，daily审计确认App/installation/token均仅metadata read、contents/pull_requests write，审计token撤销CONFIRMED。

真实主PR611首次明确后，按政策受控改名plans/codex-config-alignment/→plans/P611-codex-config-alignment/，主文件同步为[PLAN]_P611-codex-config-alignment.md；Report/Assessment用途名保持。改名前核3 tracked/0 dirty/0 untracked/0 ignored、无目标冲突和重解析点；git mv后、正文更新前逐文件摘要相同；恢复版本d6bc62b与固定提交旧路径保持，唯一活动主Plan与相对链接再核。主题与branch/task身份未变，没有借用Issue608。活动政策链接同步，后续仅记录/补号文档提交，不改变实现或平台审核有效性要求。

仓外证据：D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/codex-config-alignment/2026-10-29/，含publication-checkpoint、bootstrap/daily audit、push/create结果、权限截图及controlled rename。当前旁聊附加PR卡片工具返回thread not found，未换线程执行；实际GitHub PR可通过上方URL访问。以上为发布时历史检查点，当时未合并/未接受、主Plan active；当前合并、Q4准确接受及延期范围以下文为准，原平台Approve缺口不补造。

## 合并后收尾检查点

Owner明确“#611 PR 已合并，继续后续工作”。平台核PR611已于2026-10-29 17:12:25 Asia/Taipei合入develop；来源ce871c4ed3631174855b06e858ff1e1a8f4fa31c，merge db4a85d0aee4dd12059cfb9abf0829563b1e5397，完整tree同为45224d95ce6aba99a643c9c73b31d4b9d397e9ab。4项来源CI通过，reviews/conversation为空，未见有效Approve，不追溯补造。

正常fetch/ff-only后本地develop与origin均db4a85d，原.playwright-mcp/未跟踪目录保持；Gitee镜像从已核祖先e195bfe正常快进15提交并ls-remote读回db4a85d，未force或改remote。develop中MCP依赖按锁安装102包，Node本地协议/模拟10 passed，--check列9入口和五组变量存在，仅静态就绪；当前会话工具清单没有SSH工具，实际宿主发现/主机认证未测。新daily后台audit再次确认App/installation无Workflows write，token撤销CONFIRMED。

本轮事实文档在documentation/611-post-merge-closeout新worktree维护，base=db4a85d，不向原已合并分支追加实现。详见 [合并后报告](./[REPORT]_post_merge_closeout.md)。1218 tracked/0 dirty/0 untracked/4066 ignored的原worktree仅准备本地清理；27文件配置/状态已不透明保留，其他4039缓存/依赖可重建。当时仅准备清单；其后本会话Q5已具名授权并完成原本地工作树/分支清理，远端、备份、develop及新收尾worktree保留。

该合并后检查点起初保持active，未将“已合并，继续”推导为接受；其后Owner本轮Q4的实际接受与完成条件调整见下。本旁聊不派子Agent，独立核验不冒充完成，未测事实继续保留。

## Owner准确版本接受及完成条件调整

2026-10-29，本会话合并后Q4具名准确成品为来源ce871c4ed3631174855b06e858ff1e1a8f4fa31c及merge db4a85d0aee4dd12059cfb9abf0829563b1e5397，两者完整tree相同。问题已明确当前会话缺SSH工具、真实Codex发现/主机认证/独立上下文复核未完成、平台未见Approve；选择接受表示将上述事项移出本轮完成条件、作为后续且不补造审核。Owner明确选择“接受当前配置/离线版本，明确延期上述事项并完成 Plan”。

接受范围为本Plan配置结构、九入口/既有账户的按名配置与锁定实现、静态/离线行为、同步治理文档及已完成的Git交付；原AC1–8的配置/离线证据齐备，成果已合入develop且依赖就绪。未完成的独立复核/宿主发现/主机认证按该真实决定DEFERRED/NOT_TESTED，不计PASS，不追溯制造原PR平台Approve。准确完整基线可恢复于ce871c4的本Plan及关联报告；Q4这一完成条件调整与原AC正文分别保留，旧接受不覆盖未来改动。

AC/可用配置离线成果及Owner准确版本接受均已满足本轮调整后的完成条件，主Plan据此completed。主Plan完成不表示后续验证已执行，也不授权远程命令、权限变化、清理或未来PR合并。Q5原本地工作树/分支已另获具名授权并清理，结果见下；未将Q4接受当作删除批准。

## Q5仅本地清理结果

本会话Q5明确选择“授权上述仅本地清理，保留备份及两端远程（推荐）”，具名原worktree及本地branch maintain/codex-config-alignment，tip ce871c4、已合入db4a85d。执行前重核1218 tracked/0 dirty/0 untracked/4066 ignored、27项备份相对路径/长度一致、无重解析点/index锁/命令行路径引用；第一次预检仅因Git NUL输出末尾空项多计而在任何删除前停止，按真实格式排除空项后清单未变，不是技术拒绝。

2026-10-29 17:33:37 Asia/Taipei，经普通git worktree remove、git branch -d实际完成，均exit0；目录、worktree注册和本地分支均已不存在。未force、未改用递归删除；GitHub与Gitee原同名分支再次实时读回均ce871c4并保留。恢复tip及27文件保留在原仓外证据目录；develop、新收尾worktree、备份和其他任务保留。具体结果见postmerge-local-delete-result.json，成功项不重复。
