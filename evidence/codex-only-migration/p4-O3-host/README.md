# O3 clone：Owner信任已核实，实际调用方案待批准

## 本轮已完成

已归档6张Owner提供的原始截图及SHA256，覆盖启动、待审阅、具体条目、Trusted/[x]与Installed1/Active1。当前CLI0.147.0、gpt-5.6-sol；Source确为具名clone的`.codex/hooks.json`。没有代点信任。

Owner操作后，仅再次运行既有`topology-inventory.py inventory --topology clone`，exit0。根、src/mj_agent、tests均实际返回37项目技能，同一项目hook `enabled=true / trustStatus=trusted`，errors/warnings均空。文件身份仍为816项精确匹配与GLOSSARY.md一项既有LF/CRLF映射；三项hook链SHA与原树一致。证据见`trust-verification.json`。

这是发现、加载、人工信任与启用的证据。没有单独拍到项目级信任提示，不能虚构该过程；尚未执行clone中的hook行为canary。主副本已经通过的模型/离线测试不重跑。

## 唯一新增写入范围

具名目标（当前完全不存在）：

`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone/.venv`

hook启动器通过`uv run --frozen --no-sync python`调用纯标准库守卫。主验收副本已有Python3.13.5环境；clone没有`.venv`，本轮不尝试隐式创建或下载。建议用同一已安装CPython，仅创建标准库环境，不装pip、不安装锁定依赖、不联网：

```powershell
& 'C:/Users/Admin/AppData/Roaming/uv/python/cpython-3.13.5-windows-x86_64-none/python.exe' -B -m venv --without-pip 'C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone/.venv'
```

执行前再次核实目标为准确绝对路径、不存在、所有祖先非链接；Python身份以`canary-proposal-binding.json`为准。执行后只对新环境生成文件清单与摘要，并核验817交付映射、clone Git状态/索引及原索引，未提交文件不暂存。

新增文件限定`.venv/**`：标准venv的配置、Scripts解释器/激活脚本和Lib/Include目录等，实际清单以生成后记录为准。它不是正式交付文件，也不改变817清单或CI绑定。不得复制主副本整个环境、缓存、个人配置或凭据。

恢复：此目标原状态为不存在；保留生成文件身份和出处。后续若需要移除，只能在另行具名授权并复核清单后处理这个新环境，不整删clone或其他目录。本轮方案不包含删除。

## 单次无副作用模型canary

只在clone根执行`git status --short`，不运行其他命令、不读业务数据、不写项目文件。驱动差异为`host-O3-status-proposed.diff`；它复用v4的首个hook阻断即停止逻辑，任何非预期审批请求直接停止、不自动回应。没有新增配置、守卫或权限修改。

```powershell
& 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration/evidence/codex-only-migration/p4-O3-host/host-O3-status-proposed.py' canary --location root --model gpt-5.6-sol --canary-id O3_ROOT_STATUS
```

- 根：`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-20260918-ij3anyxq/topology clone`。
- 宿主/模型：原CLI0.147.0、gpt-5.6-sol、官方OpenAI提供者，禁止回退；仅沿用已批准模型连接。
- 保持strict-config、8MCP disabled、独立home、readOnly/networkAccess=false及180秒截止。新输出仅在既有`C:/Users/Admin/AppData/Local/Temp/mj-agent-p4-host-ci-20260920/results/l5/<时间>-O3-root-status`；Git只读命令可能正常刷新该一次性clone的索引统计，须记录差异，不动原树索引。
- 预期：宿主实际调用git status、关联project hook完成、commandExecution exit0、正确根/local指令来源与技能源、前后交付身份不变。Git报告GLOSSARY换行状态应如实保留，不修饰为clean。
- 截图信任不代替上述调用证据；模型未调用工具则NOT_TESTED。出现hook block/其他技术拒绝即停止，不改命令或工具重试，记录BLOCKED_EXECUTION_ROUTE。

此方案尚未执行。推荐批准“仅O3具名.venv准备＋一次只读canary”；它不包含O4、R1/R2保护面修复、真实服务连接或清理。P4仍未全部验收，不进入P5/P6、不发布。
