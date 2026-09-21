# P5 清理后受控复验：执行路线缺项

81 项具名删除已执行；六文件修订已批准并应用。入口、消费者、技能、资源、配置、frontmatter、wikilinks 七条清理后静态命令均 exit 0，不能代替下述未运行测试。

## 实际拒绝与影响

`verify-after.py` 在 `C:/Users/Admin/AppData/Local/Temp/p5-x95ag_4r` 创建测试容器目录成功；随后创建其 `r` 子目录时返回 `[WinError 5] Access is denied`。独立 Git 初始化、复制 817 文件、临时索引建立、audit derive 与 pytest 均尚未开始。脚本退出 0 只表示阻塞记录保存成功；验证结论为 `BLOCKED_EXECUTION_ROUTE`，测试为 `NOT_TESTED`，不是测试失败。

未在原仓创建测试 TEMP，未改其他工作树或其索引。没有尝试另一个目录、工具、参数、权限或编码。新建的空容器保留，不为收尾递归清空。当前会话不具备提权/改变沙箱权限的执行路线。

## 尚需输入与后续精确范围（本轮不执行）

需要 Owner/执行环境解决上述仓外目录的正常访问条件，或明确提供经审阅且符合相同保护要求的执行环境；新的聊天批准本身不会改变文件系统权限。不得通过改测试参数、插件、tracked-only、环境隔离或保护来规避拒绝。只恢复正常路线后再审查/执行剩余复验，不重放六文件修订或 81 项删除。

复验对象为 `delivery-after.json` 的 817 项当前公开交付（811 与清理前一致，6 个批准的文档/注释变化），排除秘密、个人配置与退役 81 项。临时副本和 pytest TEMP 必须在所有真实工作树之外；在任何可能写索引/提交的测试之前，须实际验证独立 `git init` 成功、`.git` 为目录、`rev-parse --show-toplevel` 精确等于该临时副本。只在这个独立副本中为已审阅公开 817 项建立临时 tracked 索引，不能触及原仓索引。不得直接重跑已执行的一次性 helper；应从已保存的失败边界继续，并再次核实身份。

保持 `verify-after.py` 中已审阅的封闭非秘密环境、现有依赖和受控 runner。剩余命令为独立副本的 `scripts/check_ai_context_audit.py --derive`，以及同一 Python 执行 `scripts/sdd/run_offline_pytest.py`，参数仅包含以下十份现有测试与 `-q --tb=short`：

- `tests/unit/test_sdd_development_agent.py`
- `tests/unit/test_native_governance.py`
- `tests/unit/test_native_scan_domains.py`
- `tests/unit/test_native_skill_contracts.py`
- `tests/unit/test_native_migration_guards.py`
- `tests/unit/test_codex_native.py`
- `tests/unit/test_native_mcp_scopes.py`
- `tests/unit/test_offline_execution_boundary.py`
- `tests/unit/test_check_ai_context_audit.py`
- `tests/unit/test_env_example_ascii.py`

测试中的临时 Git 操作只属于合成 fixture；不是交付提交。全部现有断言及插件限制保持。失败或技术拒绝继续如实记录。此前 CI 35564875219 仅证明清理前交付；此次没有发布、触发 CI 或运行宿主。原生执行代码、配置、守卫、37 技能未变，既有实际宿主证据仅在该身份与原批准平台范围内复用，不声称清理后重新实测。后续是否需要额外 CI 以实际受影响范围审查，不能把本文件当成发布授权。

P5 当前未完成；P6 未启动。恢复只能按具名 ZIP 成员及当前身份审查，不作全树 reset/clean。
