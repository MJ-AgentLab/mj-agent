# O2 唯一新增请求范围：根路径只读确认（待批准）

本轮O2已启动，读取技能和共享边界成功。宿主随后请求git rev-parse --show-toplevel，而O2原请求集合只含政策Select-String；驱动按范围停止，exit1，无批准响应，无重试。不是hook拒绝或项目测试断言失败。旧请求会话已关闭，不能再批准requestId=0。

实际cwd为C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/l5 native acceptance；完整command和commandActions与O1冻结根查询完全匹配，原树/主副本817项前后保持。

推荐批准host-owner-relay-v3-proposed.diff：仅在F_RUNTIME已有政策查询之外，增加同一完整git rev-parse --show-toplevel请求形态。O2仍仅允许副本根cwd；不借用O1的子目录许可。F_GIT不变。

批准差异后重新启动O2一次；实际请求出现时在本对话展示，再由Owner批准一次或取消。不因路线批准提前执行命令，不扩大至其他Git动作、参数或路径。新驱动仅AST检查，尚未运行；180秒限时、CLI0.147.0/gpt-5.6-sol、strict-config、8MCP disabled、readOnly/networkAccess=false保持。

本案不写文件、不运行真实EVAL。恢复只关闭自建会话并保留日志，无源文件回滚。若再次出现新范围/技术拒绝，停止，不自行调整保护或换工具。具体启动为原O2-READY.md命令的驱动名替换为host-owner-relay-v3-proposed.py，其他参数不变。

本次结果见O2-execution-20260921.json。O1合成技能PASS及实际CI保持；P4仍未全部验收，P5/P6不启动。
