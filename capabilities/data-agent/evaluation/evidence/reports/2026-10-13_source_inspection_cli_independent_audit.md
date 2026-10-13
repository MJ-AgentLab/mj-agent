# T-007c独立Agent合成核验

核验者/root/t007_independent_review；2026-10-13。feature/582-source-inspection-cli，base/HEAD fd045520c0123627e53d23c0ad58bf97a6b3552e，candidate UNCOMMITTED。结论VERIFIED_OFFLINE_SOFTWARE，符合获批AC-C1–8，无阻断性实现发现，供Owner接受。本报告不表示actual/来源/target/runtime或Linux/macOS原生入口通过；最终raw binding核验另由主线程记录。

独立Agent在实现前从本轮批准方案建立期望，读取真实成果/原bytes并复现；未改源码、测试、契约、Git状态或平台。临时合成材料/原日志/command/stdout/stderr/trace保留在.mj-agent-local/t007c/independent/corrected-synthetic-nantgc_l，故障记录在同级fault-protection-pytest.txt。

| AC | 独立真实结论 |
|---|---|
| C1 | main签名、keyword-only root、help和显式模式一致；missing_mode真实退出2，read/inspect/write0 |
| C2 | actual_label/unknown_source真实退出2，仅manifest read1、inspect/write0；不存在baseline未读取，无目录 |
| C3 | 七份API bytes摘要逐项复核；缺省baseline b''、提供时保持原bytes，空/非object2且inspect/write0 |
| C4 | invalid_hash真实退出2，API1次/write0/无目录；其他结构/限额反例对照真实代码和本轮测试 |
| C5 | normal/no-review/missingHP01/fictional-ref/negative-review/unknowncheck均3，单JSON；缺观测22分母/21观测/33bound，固定状态不升级 |
| C6 | normal/repeat/baseline原bytes相同；14种新进程禁止导入/网络/秘密/引用哨兵均0，无core/judges/report/runner/app/client |
| C7 | 单JSON复用原后端；独立17项fault/close/collision/parent/属性/hardlink/平台拒绝模型PASS，部分输出保留 |
| C8 | 18份保护size/SHA全部MATCH，固定输入/expected不改；章节/当前指向/历史标识/EOF反馈已修正，契约/BDD/trace范围一致 |

环境Windows原生固定NTFS，复用develop已有.venv；新进程-I -B -X utf8，明确注入候选src、无凭据白名单环境。无安装/同步依赖、秘密读取、来源引用解析、actual/live或服务连接。role事实及独立子进程载体原bytes已由主线程复制到本目录[role事实](2026-10-13_source_inspection_cli_role_facts.json)及[verifier](2026-10-13_source_inspection_cli_verifier.txt)。每case command.json给定source_root、trace、mode、argv/cwd；复现选择新输出目录。

独立故障子集命令：

    D:/workspace/10-software-project/projects/mj-agent/develop/.venv/Scripts/python.exe -B -X utf8 scripts/sdd/run_offline_pytest.py tests/unit/test_eval_runner.py -q --tb=short -k "inspection_cli_failed_delivery or inspection_cli_missing_platform_capability or inspection_cli_native_attributes or inspection_cli_hardlink"

真实exit0，17P/215deselected，0.68s。主线程358P/36W组合和BDD-only18P/36W transcript另独立读取，未冒称独立Agent重跑全套。JUnit18 testcase与scenario_test_ids精确集合对应，log/JUnit原bytes SHA匹配，0failure/error/skip，source_kind=software_test。G21真实0P/0W/0F、14DEFERRED/4SELFTEST；legacy历史证据不升级为运行或actual PASS。

原bytes摘要：
- 新inspection_runner.py：8d0fc1634d2b1abafd1c4f72d321106a8e586eb679c0c47bd673f56a824c107a
- 固定inspection.expected.json：e5e4181f78b4efc8595dbabaeead7e22cc8c65d4d864e87a59b368f91662ecda
- normal/repeat/baseline输出：6b7918d6d86f745dcad6c52d5c7fc846379b5095860582706b77f2af1d932994
- role事实：a00b82f8ffd11e78d35ddda7bbb0912c0b3067a8a4a2caf7b0eab15fdbeee761
- verifier：71975a5a4c23da6fd235cb0be8f62c574f64c0e0d5c206f87bb66b23d95ff743

首次载体预import包装器再runpy产生重复加载warning，修为只预装inspection/_file_io；第二轮误计HP01有2条review，实际1条，expected bound修为33。两次只修载体/自身预期，失败目录/日志保留，未改软件/门禁/输入补绿。

严格窗口、完整分母、same_target_replay、0.03与红线由原核心及回归保持。真实包缺失，来源/脱敏/批准/独立审阅真实性及target接受未验证；Linux/macOS原生保护延期。OPEN/active/idea/null保持，Owner最终接受和整个T-007未完成。
