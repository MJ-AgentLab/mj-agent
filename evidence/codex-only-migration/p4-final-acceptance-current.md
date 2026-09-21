# P4 技术验收收口（2026-09-21）

**结论：已批准范围内的P4必需L1–L5技术验收通过。P5/P6未启动。**

当前原树HEAD为20e2f24c352cf640d9dd33234b128ca897804b99，原索引保持、暂存为空。正式交付817项以p4-protection-remainder/R2D-delivery-binding.json为准（815不变+两项已批修复）；主L5副本相同，R3临时规则已恢复。HEAD不能恢复未提交P0–P4成果，P1共享安全测试拆分及各阶段公共备份继续保留。

| 层次 | 结论与实际边界 |
|---|---|
| L1 | 37同名技能、共享资源、正式消费者及处置来源完整；真实宿主发现证据保留 |
| L2 | 独立Git副本与原生维护/解析通过；根、子目录、空格、clone、linked实际覆盖按原记录，不把静态扫描当运行 |
| L3 | 既有离线安全证据保留；两文件修复11测试22子测试通过；当前Linux实际CI1054通过22跳过 |
| L4 | 37技能/296维/142案例静态对照；五族各一项及近邻有有界真实canary，非37项模型执行 |
| L5 | Windows CLI0.147.0/gpt-5.6-sol；hook允许/拒绝、正确保护编辑、Owner一次批准往返、异常/恢复/重入、clone/linked证据；R3独立native规则拒绝且未起进程 |

实际CI：[35560658984](https://github.com/ranzuozhou/mj-agent-p4-acceptance-20260920/actions/runs/35560658984)，commit208dfa915d9fc465b64dd7131959367df0128c26，49步骤成功；817交付+原已批两公共词表819blob身份闭合。主Tests977通过15跳过，BDD13通过7跳过，Contract64通过。旧CI及原失败轨迹不覆盖删除。

R3只在主副本追加禁止git status --short的一条临时规则。真实payload原样查询，hook完成无反馈，随后commandExecution declined、exitCode -1、processId null、duration0，输出明确policy forbids该前缀。证明规则引擎的真实独立拒绝，不代表原六条禁止规则逐一模型执行。规则恢复到ca65d2f4d6c68902571db3da280009a3ec2a9969d30803a522d13f68f5f21ff5。见p4-protection-remainder/R3-execution.json。

未测范围：workspace-write模式、Linux Codex宿主、Desktop App及其他平台；PR-only/原仓分支保护及P6交付尚未做。8个MCP真实连接、memory/生命周期、凭据写入和真实runtime EVAL属于L6/历史依赖，不纳入本次P4通过。保留旧O2模型改写失败；S1/R3仅证明有界取证客户端及时停止，不声称模型永不重试。

## P5所需具名审阅

完整逐文件表：p4-cleanup-review-final.csv，387项身份核验一致。81项旧资产条件候选另列p5-named-legacy-candidates-review.csv（含绝对路径、用途、替代者、消费者证据、SHA、恢复和授权）。其余271项保留/仅审阅、19项证据保留、16项已在P3获批移除。

**所有当前项仍不可自动删除。** P4通过不授予P5删除权；存在活动消费者的项必须保留或先完成获批替代。后续仅在P5阶段获准后按具体文件清单审阅、复核身份与恢复来源，并取得对应删除授权；不得整目录删除sdd/adapters/_common或清空证据。P5清理后验证尚未运行。

逐AC及U01–U07见p4-final-acceptance-current.json；完整累计结论见报告§53。此次未删除旧资产、未发布原仓、未进入P5/P6。
