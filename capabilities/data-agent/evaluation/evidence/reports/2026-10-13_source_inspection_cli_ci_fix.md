# PR #599 来源检查 CLI 测试平台期望修复

2026-10-13 Owner明确要求“pr 599 存在 check failing，修复”，承接已有G1 `feature/582-source-inspection-cli` 的局部测试修复、离线验证、正常提交及通过现有单仓App补推同一PR/核验CI。GitHub-only/Gitee延期决定保持；不合并、不删除、不改权限、不执行actual/live。比较head为3de8a1bc28144444a3b43474460ccaa239366e1d，base develop/fd045520c0123627e53d23c0ad58bf97a6b3552e。Owner先前接受本地软件的原bytes时点及既有报告/绑定保留；修复授权不倒写成新的业务接受或平台审核。

## 根因与修复

[push CI](https://github.com/MJ-AgentLab/mj-agent/actions/runs/38372052782) 与 [PR CI](https://github.com/MJ-AgentLab/mj-agent/actions/runs/38372152625) 绑定3de8a1b，均恰有同5个NUL参数用例失败，1698passed/164skipped/82deselected/24warnings。新增测试无条件要求backend零调用，而既有_file_io._lexical仅在Windows拒绝保留名NUL；Linux须由原_backend返回FS_CAPABILITY_UNAVAILABLE。拒绝型Mock把这一次正常后端拒绝模拟成AssertionError/INTERNAL_ERROR，backend.assert_not_called失败。原日志和实际保护代码交叉验证此原因，既有Linux入口仍fail closed。

仅修改test_eval_runner.py的test_inspection_cli_paths_refuse_before_backend：非Windows且值为NUL时，Mock包裹真实后端，要求调用一次并返回固定FS_CAPABILITY_UNAVAILABLE；其他20个跨平台用例与Windows全部25个用例仍要求backend零调用。全部路径均保持inspector零调用、不回显输入、输出不存在。参数集合、测试数量、负例及原marker均保留，没有新增SKIP或删断言。

公开API、合同、实际代码、core/schema/judges/report/_file_io/runtime/CI/守卫/权限无变更；不改变接受标准或保护。无rename/move/delete/SQL/runtime canonical变更，SPEC Delta=None。方法为A风味root-cause-first；原两次Linux CI的5FAIL为RED，本次新离线执行为GREEN，独立平台模型不是原生Linux成功入口。

## 本地验证

- 本次hardened offline相关core/inspection/CLI/BDD共358passed、36条既有第三方警告、11.96s，exit0。[原执行载体](2026-10-13_source_inspection_cli_ci_fix_execution.json)保存实际argv、环境类别、原combined stdout/stderr bytes的base64、size/SHA及exit，不归一化原日志来补绿。
- Ruff单测试文件及全仓均exit0；mypy全src通过，源码57文件。这里只记录静态类型，不表示Linux/macOS原生文件入口成功。
- 首次调用方误给父runner脚本加-I，pytest前同目录import失败；原错误载体保留本地ci-fix/launcher-failed-execution.json/raw。改用仓库文档中的正常父入口后成功，原hardened子进程、依赖/守卫/权限不改。该Python启动错误不是审批或守卫拒绝。
- 独立Agent从AC-C7建立期望、读取真实函数与原保护，25项Windows原生负例通过；另25项POSIX平台模型通过：5项NUL后端拒绝、其他20项词法早拒绝，全部inspector0且无输出。模型不计native Linux或actual验收。[独立本地检查点](2026-10-13_source_inspection_cli_ci_fix_independent.json)保留真实证据及18份保护/inspection_runner不变结论。
- 新49份版本快照见[CI修复绑定](2026-10-13_source_inspection_cli_ci_fix_binding.json)，旧47份publication绑定和原45份接受绑定保留历史；新绑定记录唯一测试版本差异，排除本报告和自身避免循环。源CLI SHA8d0fc1634d2b1abafd1c4f72d321106a8e586eb679c0c47bd673f56a824c107a保持。

## AI自检与交付边界

Scope drift=None：一个测试函数及本轮补充原bytes/独立证据；不新增业务材料、依赖、入口或保护后端。12项自检中模块、数据边界、无秘密/调试/机器绑定测试、scope、双段、commit类型、原PR模板与必要引用保持；用户行为不变，CHANGELOG/INDEX/AGENTS及合同无需新变更。5a无大改反扫对象，5b只补新证据，5c已有入口不变，5d合同无缺漏。修复拟用feature允许的test(eval)提交；实施Codex，独立Agent /root/t007_independent_review，模型/effort保持继承。

本报告为提交前本地检查点，不预填未来SHA、补推或CI成功。实际提交SHA、App执行回执和新head的五项CI，随后另存本地ci-fix结果；若新CI失败继续按真实日志修复，未完成不记通过。PR原正文保存初次发布接受基线，新增提交/报告承接本次修复，不伪造旧接受版本。

发布前只读核查发现origin/develop随#598前移至3e28069e29570263455e4f7a15faee41166508f8；新增portable/legacy delivery文档、脚本及测试，与evaluation源/后端/CI/守卫无交叉。PR599实际MERGEABLE/BEHIND，本地保留原比较基线；本次修复不执行Git或PR合并。补推后以实际当前head/base及CI事件重新核证据，不把历史fd045520写成远端最新tip，也不声称完成base集成或合并就绪。

独立GitHub MCP此前在线重取因Authentication Failed: Bad credentials标BLOCKED_EXECUTION_ROUTE，原错保留且不重试/换路线/改凭据；本轮独立Agent读取主线程已成功捕获的原API/CI记录及真实本地成果，不声称独立connector成功。平台普通补推仍只经原已核验单仓App，不扩展路线或权限。

#582 OPEN、Plan active、capability idea/last_verified=null保持；Gitee DEFERRED/NOT_EXECUTED。实际来源、脱敏/批准、target/runtime接受及Linux/macOS等价原生保护延期，没有合成转actual、采样、服务连接、merge、删除或权限变化。
