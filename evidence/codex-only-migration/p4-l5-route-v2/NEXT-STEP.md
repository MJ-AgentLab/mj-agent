# H03 有效权限不匹配后的具名选项

状态：仅准备，未执行新路线。原H03在turn/start前停止，没有模型调用。

实际返回：thread/start为readOnly、networkAccess=false；config/read只读元数据报告项目层workspace-write、on-request。说明项目配置被读取，但实际线程权限不同；原因尚未确定，不能将其直接归因于缺少Windows sandbox安装。没有读取个人配置或认证正文，没有配置写入。

## A：保留现有只读权限继续无副作用canary（推荐）

审阅host-readonly-proposed.diff。仅将测试驱动预期从workspaceWrite改为完整readOnly/networkAccess=false匹配；不改变实际权限、原配置、hook、信任、模型、MCP隔离或审批策略。原脚本保留。先执行H03一次；有真实允许轨迹后才逐项运行原冻结H02a/H02b/H04–H08（最多原3cwd×8例），拒绝或不支持按原停点处理，不发送批准回复、不自动换工具。

固定版本0.147.0、模型gpt-5.6-sol，目标仍为具名l5 native acceptance，8MCP禁用、strict-config开启。命令：绑定Python -B evidence/codex-only-migration/p4-l5-route-v2/host-readonly-proposed.py canary --location root --model gpt-5.6-sol --canary-id H03。

结果只代表当前readOnly会话；workspace-write路线仍未验收。计划§6.2五族、近邻与删除演练尚需补足，原8canary不能充当完整L5。

## B：仅继续只读诊断Windows权限来源

保持canary未运行，核对官方/本机sandbox机制与当前返回。不安装sandbox、不创建系统账号、不改权限模式或个人配置。如需工程师操作先给出具体步骤与影响再决定。

## C：保存当前证据并停止

保留已验证发现/信任与实际CI；P4未全部验收，P5/P6不启动。

需要决定的依据：原P4对技术拒绝后停止、不得自行换路线的限制。当前hook已经受信任，无需再次要求Owner信任同一未变化定义。该提案不是权限升级或自动信任请求。
