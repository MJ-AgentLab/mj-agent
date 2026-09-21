## 变更摘要

开发技能与项目配置此前依赖旧客户端源文件、投影、lock 和双工具检查。本迁移将 37 个同名开发技能、共享资源和 `.codex` 配置交给原生资产直接维护，迁出必要 MCP 启动工具，并由原生检查与保留的安全测试承接消费者验证。按具名授权删除81项旧资产；另16项测试在P3已删除，未重复清理。

正式交付候选来自 `p6/file-inventory.csv` 的 DELIVER 行，分组见 `commit-groups.json`；817项是历史原生验收集合，不是原仓完整提交集合。包含43项正式新文件，保留非客户端 adapter、业务资产、安全断言和恢复材料。

> 交付基线：`20e2f24c352cf640d9dd33234b128ca897804b99`；head分支`maintain/codex-dev-mode-migration`，base明确为`develop`。Owner已批准本交付包；政策季度审计单行已准确应用并复验通过。提交与CI的准确SHA由实际发布记录及PR checks绑定，不把准备时的基线当作最终提交。

## 影响评估

- 开发控制面：AGENTS、原生技能/config/hooks/rules、MCP启动器、冻结infra契约、政策/SDD及CI直接消费者同步切换。权限、信任和Owner决策并未因直接维护而取消。
- 应用：仅 `env_drift.py` 模块说明变更，去除docstring后的AST与HEAD相同。SQL、Prompt、runtime skill正文、catalog、生产配置和数据库行为不变；不承接#499/#552剩余工作，也不关闭它们。
- 平台：已有Windows CLI0.147.0只读宿主具名canary和Linux离线/Ubuntu CI证据；Desktop、workspace-write、Linux Codex宿主、其他OS及L6外部服务未验证。
- P6新增17份文档/示例修订。35技能身份未变，另2技能仅修正可选署名示例并做八维静态复核；没有对新两份字节运行模型canary。守卫/config/启动器字节未变，真实宿主证据仅在原批准范围复用。

## 审核要点

1. 原生所有权、37入口、允许8项MCP及biz/ssh永久禁入；凭据只传变量名，应用与MCP凭据分离。
2. 原生检查承接保护语义；真实hook/rule拦截、模型自述、静态检查和Owner批准分别记证，拒绝时不绕过。
3. 97项删除与81+16具名集合一致；43个正式新文件完整，未将全部未跟踪/证据目录或资产表行纳入提交。
4. 政策单行已获准并闭合；最终CI必须绑定原仓新提交，不复用旧私有CI为最终绿灯。

## 自检结果

- [x] 配置语法/原生结构：P5既有结果按身份复用，本轮原生检查STATIC_PASS。
- [x] 工作流已随P3批准组同步；P6不修改CI gate，最终CI待实际push/PR。
- [x] 新增文档差异无真实秘密；个人/秘密资产仅元数据排除，不读取正文。
- [x] G1/G2已由Owner分别提交为 `e5f99c87a50ad47856a41f40c2acccf75a5534da` / `1eb9257f15ee250b732f5db8a7f0b4266c0d2401`；G3准确212路径已暂存待提交，历史证据空白检查失败已披露。提交类型为 `infra` / `docs`，CHANGELOG已更新Unreleased。

## 文档自检（按 track）

### Code-Side（A1–A6 / OB1–OB5）

- [x] A1–A3：原生文档路径与类型保持，frontmatter检查142份通过。项目根Markdown按既有例外，不补frontmatter。
- [x] A4–A5：归档引用0违规、五根文件链接0缺失，新增交接指针进入docs/INDEX；P6最终包文件链接另做存在性核对。
- [x] A6：根及局部AGENTS与P5身份相同；P6指南记录既有边界，没有更改入口规则。
- [x] OB1–OB5：指南约420行，历史更新表保留，技术/版本/服务状态分别报告；无新增正式文档体系。历史GLOSSARY换行warning保留。
- [x] 政策审计行与原生模板措辞闭合：准确批准补丁已应用，frontmatter/链接/diff复验通过。

### Agent-Side（A7–A11）

- [x] N/A：本迁移没有修改runtime SKILL/PROMPT正文、loader契约或EVAL数据；不将开发canary当runtime EVAL。
- [x] A11原有状态保留；没有新增或取消waiver。

### Engineering-Workflow（A12–A14）

- [x] A12：37技能schema、触发及资源检查通过；两份署名示例当前八维静态审阅，未声称新字节模型执行。
- [x] A13：既有实际保护证据按未变guard/config身份复用，P6不改变权限/信任；新政策文档单行已获准应用并验证。
- [x] A14：项目MCP与既有凭据模式保持，8项结构STATIC_PASS；不把静态成功标为服务已连接。
- [x] maintain风险：冻结infra、契约、启动器与CI历史批准可追溯；P6普通文档修订及新增受保护政策单行均已获具名批准并复验；未改变守卫、权限或CI门禁。

## AI Self-Check Checklist

- [x] Codex参与：执行P0–P6累计已授权工作；P6负责范围/证据核对、17文档修订、静态检查、交付草案。
- [x] HITL scenario hit：原生控制面、契约、CI、批量迁移；新政策行及原仓stage/commit/push/PR/CI已获本轮具名批准。
- [x] BDD/TDD impact：安全断言与P1拆分保留；P6无代码行为变化和新测试，复用P5受控265测试/22子测试/零skip。
- [x] Subagent dispatched：P6 `consumer_review` 只读探索与diff复核，无编辑、测试、网络或Git写入；其他阶段按累计报告分别记录。

## HITL Trigger Inventory

- [ ] sql-guardrail-relax — No；SQL guardrail/precheck未改。
- [ ] runtime-skill-content-change — No；runtime技能正文未改。
- [ ] prompt-version-or-body-change — No；system Prompt未改。
- [ ] biz-catalog-sync — No；catalog未改。
- [x] mcp-server-trust-posture-change — Yes；P3批准的原生config/guard/启动器/冻结infra迁移及P4具名兼容修复，证据见累计§15–16、§50。P6没有新信任/配置变更。
- [x] declared-contract-change — Yes；P3批准组与P4 G19两行修复，累计§15、§20，保持契约/技能/摘要一致。
- [ ] database-migration — No；无schema/DDL/memory迁移。
- [ ] secrets-grants-or-prod-config — No；无真实凭据包、GRANT、生产Compose、Dockerfile外部镜像修改。
- [x] ci-blocking-gate-toggle — Yes；P3整组原生检查替换与批准门禁映射；P6不改门禁。
- [x] bulk-content-purge-or-migration — Yes；P3迁移与16项旧机制测试退役、P5准确81项删除均具名授权；本轮不增加删除。

额外procedural HITL：ADR-040原有批准记录保留；本次政策单行、最终暂存/提交/双推/PR及CI触发已按 `DELIVERY-REVIEW.md` 获具名批准。人工merge不在本次请求内。

## Docker Impact

- [ ] no — 不选：`.dockerignore` 构建上下文排除规则有迁移相关变化。
- [ ] yes — Dockerfile非外部镜像行 / compose.yaml / override.yml修改：No，这些文件未改；实际影响为 `.dockerignore` 排除原生开发配置/候选与保留历史构建约束。
- [ ] yes — Dockerfile外部registry镜像引用修改：No。
- [ ] yes — compose.prod.yml修改：No。

未构建/部署新镜像；Docker相关契约/指南的原生路径引用按P3已批准范围处理。

## 验证与当前结果

P5清理后：265 passed、22 subtests passed、零skip；七项静态检查通过。P6：`check_frontmatter.py`、`check_wikilinks.py`、`check_native_skills.py --surface skills/resources`、`check_native_governance.py --surface entries/consumers`、`check_codex_native.py`、`git diff --check`，八命令均exit0。命令/环境/输出见 `verification.json`。G1/G2提交已核实；G3准确212路径的暂存及检查结果见累计报告§65，最终CI尚未触发。

G3完整 `git diff --cached --check` 返回2：2161条诊断均来自17份历史补丁与3份P2历史Markdown，20文件与批准时字节完全一致。按保留历史证据要求不改写原文，保留失败结果；未修改Git空白配置或CI gate。G1/G2暂存检查通过，不能替代G3本次失败。此项不是最终CI结果，最终CI仍须实际运行。

清理前私有CI：run35564875219，commit `40b470320ef9cf073f0d18867ca6134fa95637d2`，1054 passed、22 skipped；这是历史清理前证据，不能证明当前最终交付。原仓迁移分支尚无CI。外部依赖skip、未测平台、继承警告均保留。

远端有效develop ruleset：要求`ci`、strict同步、至少1审批、last-push审批、review线程解决、仅merge合并。审批和CI结果将绑定实际新提交；本草案无虚构PR编号、review或merge SHA。

## 恢复与交接

原生维护与Owner凭据/信任边界见Developer Onboarding §4/§6.4。HEAD目前覆盖已提交G1/G2，G3及未交付历史材料仍须独立恢复；P0–P4公共备份及增量保留迁移工作字节；P5用legacy-81-before.zip和consumer-six-before.zip；P6用before.zip、additional-before.zip及三文件中间备份。恢复先核对适用身份，按后续增量逆序评估，旧P3整组差异不直接套当前树。

本PR不自动合并、部署、关闭#499/#552或删除worktree/branch。计划生命周期保持draft，最终人工合并和交接完成后才按实际处理。
