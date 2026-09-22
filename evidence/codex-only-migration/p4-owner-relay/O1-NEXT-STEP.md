# O1 本轮执行结果与唯一待决增量

O1 已按批准路线执行，实际 exit 1；没有批准响应、没有自动重试。宿主执行了两次只读资源读取，项目 hook 三次完成后提出 git rev-parse --show-toplevel 的正常审批。驱动核对发现 cwd 不在原批准的“仅副本根”集合，立即停止。该停止是范围前检，不是项目测试断言失败。

实际请求 cwd：C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance/src/mj_agent。已确认是同一 817 项交付副本中的真实目录，非链接；完整 command 和 commandActions 与此前冻结请求一致。原树/主副本 817 项、HEAD、空索引复核未变。原请求进程已关闭，requestId=0 不可再批准或重用。

## 推荐具体选择

批准 host-owner-relay-v2-proposed.diff：仅对 F_GIT 增加上面的 src/mj_agent 作为第二个精确 cwd；原副本根继续保留。仍只接受 git rev-parse --show-toplevel 的完整已核实请求形态，不允许其他命令、路径或会话/永久规则变更。F_RUNTIME 未变且不启动。

批准差异后，助手重新启动一次 O1；新实际请求出现时再展示给 Owner 单次判断，不因本次路线批准提前发 accept。正常路线技术拒绝/新不匹配再次停止，不擅自改工具/命令/参数重试。

宿主仍 CLI0.147.0/gpt-5.6-sol，strict-config、8 MCP disabled、readOnly/networkAccess=false、180秒限时保持。测试目标写入集合为空。恢复只需关闭自建会话并保留日志；无交付文件需要回滚。旧驱动和实际失败轨迹均保留；新驱动只 AST 解析，尚未运行。

执行证据：O1-execution-20260921.json。具体差异：host-owner-relay-v2-proposed.diff。P4仍未全部验收；不运行P5/P6，不重跑实际CI。
