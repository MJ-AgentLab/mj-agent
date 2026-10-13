# #599 T-007c 合并后软件核验

本报告记录已核实的集成与离线软件事实，不是actual/runtime或整个capability接受。新文档候选位于documentation/582-t007c-post-merge，base891fd5e，未提交/推送/创建PR；原报告及UNCOMMITTED等记录保留原时点。

## 平台与版本

- [PR #599](https://github.com/MJ-AgentLab/mj-agent/pull/599)实际MERGED，merge891fd5e5c9d7f6c485ca48f468ad18e830c5af4f，2026-10-13T09:47:10Z；最终head424bed0b3694a77fc9ac08ab628335a4cd9fa096，base3e28069e29570263455e4f7a15faee41166508f8。
- 真实APPROVED绑定该head，由Owner ranzuozhou于09:47:01Z作出，早于merge；平台作者为mj-agent-delivery-executor[bot]，不同身份。平台批准、集成和原本地软件接受分别记录，不补造新的实际来源或target接受。
- 最终五项CI全SUCCESS。PR tested commit e2043eb5f1df30ff4c56b8501faaa910992983f5的父[3e28069,424bed0]与event head/base精确匹配；C3旧base身份失败及更早五条NUL失败保留，不倒写成通过。
- merge父[3e28069,424bed0]，tree2df7827966fa06e1cd46737e0b9a47549c7ea463与head424完全相同。原C4的57份Git内容对象匹配，指纹1010cfc06ee24e081ab25038180f2e7d8398a871e5838e669c57e745cc2508a2；这是内容绑定复用，不把旧记录head改成merge SHA。

## 新鲜合并版验证

[原执行载体](2026-10-13_source_inspection_cli_post_merge_execution.json)保存实际891fd5e上的hardened离线命令、原combined stdout/stderr的base64、size/SHA和exit。Windows相关core/inspection/CLI/BDD共358passed，36条既有gherkin依赖告警保留，12.44s，exit0；这不是actual/live或Linux/macOS成功入口证据。

18份保护文件及CLI原bytes保持；inspection_runner SHA8d0fc1634d2b1abafd1c4f72d321106a8e586eb679c0c47bd673f56a824c107a。独立Agent从AC核真实merge/tree/保护、原平台记录及执行载体；此前GitHub MCP认证拒绝原错保留、不重试或换路线，平台核验区分主线程原API记录审阅与独立在线重取。独立检查点另存本地.mj-agent-local/599-post-merge/independent-audit.md/json。

## 收尾逐项结果

| 项目 | 当前事实 |
|---|---|
| PR与有效head批准 | 已核MERGED及实际APPROVED，五项CI全绿 |
| develop同步 | 原3e28069正常ff至891fd5e；trackedclean，仅既有.playwright-mcp未跟踪，未触碰 |
| Gitee镜像 | 本任务继续DEFERRED/NOT_EXECUTED；当前只读develop tip3e28069，feature引用不存在，未探测或更改鉴权 |
| 原feature树/分支 | 本地与origin仍存在，保留；没有新删除授权，未删除，不处理其他工作树 |
| #589/#595与97旧备份 | 保留原收尾，不重复清理或把历史逐项核验冒称本轮复核 |
| CHANGELOG/文档 | 新G1仅同步已集成事实、入口及补充证据；候选未发布 |
| follow-up/EVAL开单 | 剩余项在#582内准备；未发布Issue/评论，无runtime正文改动触发的新EVAL backlog |
| schedule/自动化 | 没有新的调度请求或必要触发，未创建 |
| 权限/token | 不改权限；本会话既有App补推回执撤销CONFIRMED，无新App通道或权限操作 |
| Plan/capability | #582 OPEN、Plan active、capability idea/last_verified=null；不由merge自动完成 |
| actual/target/平台原生成功入口 | DEFERRED/UNVERIFIED；当前没有获批脱敏观测包，不再次索取不存在材料 |

下一项只准备[真实观测包材料契约与门禁提案](2026-10-13_t007_actual_material_proposal.md)，不在此实现actual入口或改schema、核心、judges、report、文件保护后端、runtime、CI、守卫。严格窗口、完整分母、same_target_replay、0.03、红线与来源/数据边界保持；其他target/probe-fixture原scope不变。

## 文档与原bytes

文档候选只更新Plan当前检查点、package当前状态说明、tasks/RUNBOOK/两处INDEX/CHANGELOG，并新增本报告、提案、执行载体与[候选绑定](2026-10-13_source_inspection_cli_post_merge_binding.json)。现有合同/API不变，package版本0.8/draft、Plan active与idea/null保持；历史验收报告/绑定不修改。独立核验及候选前述静态校验结果在本地outcome中单列，不预填提交/发布或新Owner接受。
