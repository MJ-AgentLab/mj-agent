# P2：37 项八维对照

所有结论为 STATIC_PASS；不是技能实际调用。源为基线原始技能，18投影仅参考。
完整逐行差异见 p2-source-candidate.diff；严格YAML前后文本、来源/候选摘要与完整章节清单见 p2-skill-comparison.json。

## S01 mj-agent-doc-author
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-author/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-author/SKILL.md`；部署 `.agents/skills/mj-agent-doc-author/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-author/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 已确定类型与scope的一份文档；原文件细节/模板见来源正文及逐行diff。 | 已确定类型与scope的一份文档 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 类型、主题、路径、真实代码、模板；原文件细节/模板见来源正文及逐行diff。 | 类型、主题、路径、真实代码、模板 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 原Quick Reference/ADR Numbering仍指docs/adr和硬编码下一号；根客户端文档为CLAUDE.md；正文12类型、9模板、Q-B1完整。 | 读规范/模板/代码；写单文档及必要INDEX/入口 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 前置ADR/SPEC判定→track→目录→模板→同名冲突→正文→B停点→校验→索引；原文件细节/模板见来源正文及逐行diff。 | 前置ADR/SPEC判定→track→目录→模板→同名冲突→正文→B停点→校验→索引 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原Q-B1保留Owner审批，但另列“跳过B流程直接写”选项，与硬停冲突。 | 目录歧义/覆盖/Q-B1；B正文先propose；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 同名冲突不覆盖，校验失败定位后重跑；原文件细节/模板见来源正文及逐行diff。 | 同名冲突不覆盖，校验失败定位后重跑；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 类型/track/命名/引用/校验逐项有结论；原文件细节/模板见来源正文及逐行diff。 | 类型/track/命名/引用/校验逐项有结论 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage6独立或返回doc-plan调用者；不提交；原文件细节/模板见来源正文及逐行diff。 | Stage6独立或返回doc-plan调用者；不提交；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S02 mj-agent-doc-migrate
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-migrate/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-migrate/SKILL.md`；部署 `.agents/skills/mj-agent-doc-migrate/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-migrate/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | canonical大/小版本归档与skeleton延迟promote；原文件细节/模板见来源正文及逐行diff。 | canonical大/小版本归档与skeleton延迟promote | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 旧/新版本、state、引用集合、归档意图；原文件细节/模板见来源正文及逐行diff。 | 旧/新版本、state、引用集合、归档意图 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读全引用；移旧doc到archive并改state/banner/INDEX；原文件细节/模板见来源正文及逐行diff。 | 读全引用；移旧doc到archive并改state/banner/INDEX | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 分析→迁移计划→标准或skeleton模式→living/frozen引用分类→INDEX→校验；原文件细节/模板见来源正文及逐行diff。 | 分析→迁移计划→标准或skeleton模式→living/frozen引用分类→INDEX→校验 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 移动/版本状态/多引用变更按D-04批准；原文件细节/模板见来源正文及逐行diff。 | 移动/版本状态/多引用变更按D-04批准；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原版本/引用冲突及D-04；缺显式目标身份变化/部分移动/重入规则。 | 冲突/部分移动先对账；保留旧/新内容与引用恢复清单；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 旧deprecated/新目标状态正确，living/frozen引用和INDEX闭合；原文件细节/模板见来源正文及逐行diff。 | 旧deprecated/新目标状态正确，living/frozen引用和INDEX闭合 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回PR文档审核或独立结束；不发版；原文件细节/模板见来源正文及逐行diff。 | 返回PR文档审核或独立结束；不发版；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S03 mj-agent-doc-plan
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-plan/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-plan/SKILL.md`；部署 `.agents/skills/mj-agent-doc-plan/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-plan/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 文档需求与Documentation Decision缺口评估；原文件细节/模板见来源正文及逐行diff。 | 文档需求与Documentation Decision缺口评估 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | diff、Issue、SPEC、已有docs、变更scope；原文件细节/模板见来源正文及逐行diff。 | diff、Issue、SPEC、已有docs、变更scope | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读代码/文档；只产矩阵和任务清单；原文件细节/模板见来源正文及逐行diff。 | 读代码/文档；只产矩阵和任务清单 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | scope→类型判定→track/风味→缺口矩阵→任务列表；原文件细节/模板见来源正文及逐行diff。 | scope→类型判定→track/风味→缺口矩阵→任务列表 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 歧义先澄清；B需求记停点不写runtime；原文件细节/模板见来源正文及逐行diff。 | 歧义先澄清；B需求记停点不写runtime；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 已有文档重叠则更新建议；证据不足不硬造新文档；原文件细节/模板见来源正文及逐行diff。 | 已有文档重叠则更新建议；证据不足不硬造新文档；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每个受影响对象有create/update/none及理由；原文件细节/模板见来源正文及逐行diff。 | 每个受影响对象有create/update/none及理由 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage4/8调用返回原步骤；建议author，不自动写；原文件细节/模板见来源正文及逐行diff。 | Stage4/8调用返回原步骤；建议author，不自动写；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S04 mj-agent-doc-review
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-review/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-review/SKILL.md`；部署 `.agents/skills/mj-agent-doc-review/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-review/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | PR文档质量与双段自检；原文件细节/模板见来源正文及逐行diff。 | PR文档质量与双段自检 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | PR/diff、branch type、plan、受影响docs；原文件细节/模板见来源正文及逐行diff。 | PR/diff、branch type、plan、受影响docs | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读PR/文档/代码，产review草案；原文件细节/模板见来源正文及逐行diff。 | 只读PR/文档/代码，产review草案 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 分类→code-doc映射→ADR/SPEC→逐文档校验→反扫→PR双段→A12-A14；原文件细节/模板见来源正文及逐行diff。 | 分类→code-doc映射→ADR/SPEC→逐文档校验→反扫→PR双段→A12-A14 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 审阅不等于发布；缺证据标未知；原文件细节/模板见来源正文及逐行diff。 | 审阅不等于发布；缺证据标未知；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 缺doc/断链逐条反馈，不自动修代码或发评论；原文件细节/模板见来源正文及逐行diff。 | 缺doc/断链逐条反馈，不自动修代码或发评论；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | A1-A14/OB和双段有依据、风险与缺口；原文件细节/模板见来源正文及逐行diff。 | A1-A14/OB和双段有依据、风险与缺口 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage15子流程返回调用者；独立输出本地报告；原文件细节/模板见来源正文及逐行diff。 | Stage15子流程返回调用者；独立输出本地报告；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S05 mj-agent-doc-sync
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-sync/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-sync/SKILL.md`；部署 `.agents/skills/mj-agent-doc-sync/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-sync/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 代码变更引起的文档更新/引用修复；原文件细节/模板见来源正文及逐行diff。 | 代码变更引起的文档更新/引用修复 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | diff、旧新符号/路径、plan文档范围；原文件细节/模板见来源正文及逐行diff。 | diff、旧新符号/路径、plan文档范围 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读代码和反向引用；写获准docs/INDEX/AGENTS主题入口；原文件细节/模板见来源正文及逐行diff。 | 读代码和反向引用；写获准docs/INDEX/AGENTS主题入口 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 映射→内容更新→全引用修复→索引/入口同步→校验；原文件细节/模板见来源正文及逐行diff。 | 映射→内容更新→全引用修复→索引/入口同步→校验 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 超plan范围/入口大改D-03与B正文先批准；原文件细节/模板见来源正文及逐行diff。 | 超plan范围/入口大改D-03与B正文先批准；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 找不到真实符号停对应更新；部分更新逐文档恢复；原文件细节/模板见来源正文及逐行diff。 | 找不到真实符号停对应更新；部分更新逐文档恢复；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每处映射/旧引用有处理且校验结果真实；原文件细节/模板见来源正文及逐行diff。 | 每处映射/旧引用有处理且校验结果真实 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage8或self-review委派返回；不commit；原文件细节/模板见来源正文及逐行diff。 | Stage8或self-review委派返回；不commit；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S06 mj-agent-doc-validate
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-validate/SKILL.md`；投影参考 `.agents/skills/mj-agent-doc-validate/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-doc-validate/SKILL.md`；部署 `.agents/skills/mj-agent-doc-validate/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-doc-validate/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 既有文档格式/元数据/链接审核；原文件细节/模板见来源正文及逐行diff。 | 既有文档格式/元数据/链接审核 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 文件集合、track、当前规范；原文件细节/模板见来源正文及逐行diff。 | 文件集合、track、当前规范 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读docs与两个校验脚本输出；产A1-A14/OB表；原文件细节/模板见来源正文及逐行diff。 | 只读docs与两个校验脚本输出；产A1-A14/OB表 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | frontmatter→wikilinks→半自动OB→track分组→根例外→报告；原文件细节/模板见来源正文及逐行diff。 | frontmatter→wikilinks→半自动OB→track分组→根例外→报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 校验授权不含修复/发布；保护面只报告；原文件细节/模板见来源正文及逐行diff。 | 校验授权不含修复/发布；保护面只报告；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 解析失败FAIL；缺工具UNMET，不拿skip补绿；原文件细节/模板见来源正文及逐行diff。 | 解析失败FAIL；缺工具UNMET，不拿skip补绿；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每项PASS/FAIL/WARN/SKIP及来源；静态审阅明确标记；原文件细节/模板见来源正文及逐行diff。 | 每项PASS/FAIL/WARN/SKIP及来源；静态审阅明确标记 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回author/sync/review调用者；不跨Stage10；原文件细节/模板见来源正文及逐行diff。 | 返回author/sync/review调用者；不跨Stage10；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S07 mj-agent-flow-diagnose
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-diagnose/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-diagnose/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-diagnose/SKILL.md`；部署 `.agents/skills/mj-agent-flow-diagnose/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-diagnose/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 难复现/flaky/perf根因诊断；原文件细节/模板见来源正文及逐行diff。 | 难复现/flaky/perf根因诊断 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 失败输入、环境、最小反馈、目标代码；原文件细节/模板见来源正文及逐行diff。 | 失败输入、环境、最小反馈、目标代码 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读repro/日志；写最小回归及获准修复/临时插桩；原文件细节/模板见来源正文及逐行diff。 | 读repro/日志；写最小回归及获准修复/临时插桩 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 先红信号→最小化→3-5可证伪假设→单变量→回归先行→修复→清理归因；原文件细节/模板见来源正文及逐行diff。 | 先红信号→最小化→3-5可证伪假设→单变量→回归先行→修复→清理归因 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 4专属面先propose；live repro须明确授权；原文件细节/模板见来源正文及逐行diff。 | 4专属面先propose；live repro须明确授权；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 无法确定性复现不声称修复；清理DEBUG，不掩盖失败；原文件细节/模板见来源正文及逐行diff。 | 无法确定性复现不声称修复；清理DEBUG，不掩盖失败；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 原红信号与回归双绿，根因有证据；原文件细节/模板见来源正文及逐行diff。 | 原红信号与回归双绿，根因有证据 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回implement Step3b或独立诊断；verify只建议；原文件细节/模板见来源正文及逐行diff。 | 返回implement Step3b或独立诊断；verify只建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S08 mj-agent-flow-implement
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-implement/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-implement/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-implement/SKILL.md`；部署 `.agents/skills/mj-agent-flow-implement/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-implement/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 已确认Plan/SPEC的Stage8编码；原文件细节/模板见来源正文及逐行diff。 | 已确认Plan/SPEC的Stage8编码 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | Plan/SPEC/Issue、repo-scan、diff；原文件细节/模板见来源正文及逐行diff。 | Plan/SPEC/Issue、repo-scan、diff | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读需求/代码；按scope写A代码/C配置候选，B先草案；原文件细节/模板见来源正文及逐行diff。 | 读需求/代码；按scope写A代码/C配置候选，B先草案 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | context→A/B/C→red-green或root-cause或infra→fresh证据→返回；原文件细节/模板见来源正文及逐行diff。 | context→A/B/C→red-green或root-cause或infra→fresh证据→返回 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原B先Owner；infra healthcheck/compose/secret同步写成必须执行；可选superpowers增强。 | B永远Owner；infra live/secret/镜像按保护面；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 红不稳定先诊断；不吞异常、不关闭测试；缺live留未验证；原文件细节/模板见来源正文及逐行diff。 | 红不稳定先诊断；不吞异常、不关闭测试；缺live留未验证；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 原fresh证据规则保留；description同时称不执行命令，与red-green步骤存在张力。 | 实现与plan一致，方法轨迹和本次证据明确 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage8结束；建议Stage10，禁止自动Git发布；原文件细节/模板见来源正文及逐行diff。 | Stage8结束；建议Stage10，禁止自动Git发布；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S09 mj-agent-flow-intake
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-intake/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-intake/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-intake/SKILL.md`；部署 `.agents/skills/mj-agent-flow-intake/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-intake/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage0原始需求受理；原文件细节/模板见来源正文及逐行diff。 | Stage0原始需求受理 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 用户目标、现状、影响对象与约束；原文件细节/模板见来源正文及逐行diff。 | 用户目标、现状、影响对象与约束 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读需求/代码；输出Intake/issue草案；原文件细节/模板见来源正文及逐行diff。 | 只读需求/代码；输出Intake/issue草案 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 类型→scope→真歧义→术语→7模块→可测AC→风险→拆分文档→HITL→草案；原文件细节/模板见来源正文及逐行diff。 | 类型→scope→真歧义→术语→7模块→可测AC→风险→拆分文档→HITL→草案 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 模糊关键scope先问；10停点及Docker镜像显式勾选；原文件细节/模板见来源正文及逐行diff。 | 模糊关键scope先问；10停点及Docker镜像显式勾选；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 未决只阻塞相关决策，不能补造AC/授权；原文件细节/模板见来源正文及逐行diff。 | 未决只阻塞相关决策，不能补造AC/授权；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | Intake含风险/边界/文档/停点/可验证AC；原文件细节/模板见来源正文及逐行diff。 | Intake含风险/边界/文档/停点/可验证AC | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，建议git-issue；不创建issue；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，建议git-issue；不创建issue；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S10 mj-agent-flow-plan
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-plan/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-plan/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-plan/SKILL.md`；部署 `.agents/skills/mj-agent-flow-plan/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-plan/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage4完整working-plan正文；原文件细节/模板见来源正文及逐行diff。 | Stage4完整working-plan正文 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | Issue、repo-scan事实、SPEC、AC；原文件细节/模板见来源正文及逐行diff。 | Issue、repo-scan事实、SPEC、AC | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读锚点与代码；先输出plan草案，批准后落盘；原文件细节/模板见来源正文及逐行diff。 | 读锚点与代码；先输出plan草案，批准后落盘 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | context→任务拆分→doc-plan→风险→验证→完成标准关联；原文件细节/模板见来源正文及逐行diff。 | context→任务拆分→doc-plan→风险→验证→完成标准关联 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | Plan正文落盘需Owner；B及保护面单列；原文件细节/模板见来源正文及逐行diff。 | Plan正文落盘需Owner；B及保护面单列；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 事实变化返回scan；不靠写plan掩盖缺输入；原文件细节/模板见来源正文及逐行diff。 | 事实变化返回scan；不靠写plan掩盖缺输入；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 任务/顺序/风险/验证/AC/文档矩阵完整；原文件细节/模板见来源正文及逐行diff。 | 任务/顺序/风险/验证/AC/文档矩阵完整 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner/原调用者；Stage5/6为建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner/原调用者；Stage5/6为建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S11 mj-agent-flow-post-merge
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-post-merge/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-post-merge/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-post-merge/SKILL.md`；部署 `.agents/skills/mj-agent-flow-post-merge/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-post-merge/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage17已合并PR收尾；原文件细节/模板见来源正文及逐行diff。 | Stage17已合并PR收尾 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | PR state/merge SHA/关联issue/plan/当前清理身份；原文件细节/模板见来源正文及逐行diff。 | PR state/merge SHA/关联issue/plan/当前清理身份 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读PR/分支；拟issue关闭/日志/followup/清理/sync/状态差异；原文件细节/模板见来源正文及逐行diff。 | 读PR/分支；拟issue关闭/日志/followup/清理/sync/状态差异 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 确认MERGED→关联issue→CHANGELOG→followup→EVAL→schedule建议→delete→sync→plan→交接；原文件细节/模板见来源正文及逐行diff。 | 确认MERGED→关联issue→CHANGELOG→followup→EVAL→schedule建议→delete→sync→plan→交接 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原followup/EVAL/plan需user确认，但有auto-issue/自动completed概述与镜像必做表达。 | 每个外部/删除/push/state动作核具体授权和hook路线；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原Step8存在发现工作树不一致就reset-hard的恢复建议。 | PR未合并早停；重入逐项对账不重复开单；未知不reset；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每项完成/未执行/阻塞有证据，不能笼统收尾完成；原文件细节/模板见来源正文及逐行diff。 | 每项完成/未执行/阻塞有证据，不能笼统收尾完成 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 独立结束或返回调用者；不递归commit/push/PR；原文件细节/模板见来源正文及逐行diff。 | 独立结束或返回调用者；不递归commit/push/PR；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S12 mj-agent-flow-repo-scan
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-repo-scan/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-repo-scan/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-repo-scan/SKILL.md`；部署 `.agents/skills/mj-agent-flow-repo-scan/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-repo-scan/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage3对Issue/Plan事实核查；原文件细节/模板见来源正文及逐行diff。 | Stage3对Issue/Plan事实核查 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | Issue、Plan、git身份、真实文件；原文件细节/模板见来源正文及逐行diff。 | Issue、Plan、git身份、真实文件 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 严格只读repo/diff/docs；产Evidence Map/矩阵/verdict；原文件细节/模板见来源正文及逐行diff。 | 严格只读repo/diff/docs；产Evidence Map/矩阵/verdict | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 追踪锚→worktree→8维scan→反扫→doc矩阵→plan verdict→验证/HITL；原文件细节/模板见来源正文及逐行diff。 | 追踪锚→worktree→8维scan→反扫→doc矩阵→plan verdict→验证/HITL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 不编码/不改plan；受限数据只经工具链；原文件细节/模板见来源正文及逐行diff。 | 不编码/不改plan；受限数据只经工具链；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 陈旧输入标需更新；未见证据不下通过结论；原文件细节/模板见来源正文及逐行diff。 | 陈旧输入标需更新；未见证据不下通过结论；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 8维事实与逐项来源、文档决策/风险/下一输入齐；原文件细节/模板见来源正文及逐行diff。 | 8维事实与逐项来源、文档决策/风险/下一输入齐 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Stage4/6请求者，不自动执行；原文件细节/模板见来源正文及逐行diff。 | 返回Stage4/6请求者，不自动执行；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S13 mj-agent-flow-review-respond
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-review-respond/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-review-respond/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-review-respond/SKILL.md`；部署 `.agents/skills/mj-agent-flow-review-respond/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-review-respond/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage15回应自己的PR反馈/CI失败；原文件细节/模板见来源正文及逐行diff。 | Stage15回应自己的PR反馈/CI失败 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 自有PR、comments、head、CI日志、Plan/SPEC；原文件细节/模板见来源正文及逐行diff。 | 自有PR、comments、head、CI日志、Plan/SPEC | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读反馈；产分类/修改方案/reply草案，发布另授权；原文件细节/模板见来源正文及逐行diff。 | 读反馈；产分类/修改方案/reply草案，发布另授权 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | fetch→逐条分类→影响→修复计划→逐条回复→风险输出；原文件细节/模板见来源正文及逐行diff。 | fetch→逐条分类→影响→修复计划→逐条回复→风险输出 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原after Owner拍板auto-post gh/MCP，容易把方案批准当作发布授权。 | req/API/schema/权限/B改动先Owner；发帖明确授权；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | head变化重新审；获取失败未验证；不发重复回复；原文件细节/模板见来源正文及逐行diff。 | head变化重新审；获取失败未验证；不发重复回复；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每条comment有采纳/解释/延后理由及草案；原文件细节/模板见来源正文及逐行diff。 | 每条comment有采纳/解释/延后理由及草案 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner/调用者；不自动commit或修改runtime；原文件细节/模板见来源正文及逐行diff。 | 返回Owner/调用者；不自动commit或修改runtime；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S14 mj-agent-flow-scope-drift
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-scope-drift/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-scope-drift/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-scope-drift/SKILL.md`；部署 `.agents/skills/mj-agent-flow-scope-drift/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-scope-drift/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage9 diff对批准scope漂移检查；原文件细节/模板见来源正文及逐行diff。 | Stage9 diff对批准scope漂移检查 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | Plan/SPEC/Issue、当前diff；原文件细节/模板见来源正文及逐行diff。 | Plan/SPEC/Issue、当前diff | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读每文件diff；产映射和continue/amend/split建议；原文件细节/模板见来源正文及逐行diff。 | 只读每文件diff；产映射和continue/amend/split建议 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 定位锚→diff→逐文件映射/风味→严重度→建议；原文件细节/模板见来源正文及逐行diff。 | 定位锚→diff→逐文件映射/风味→严重度→建议 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 超scope只建议，不自行改Plan/B面；原文件细节/模板见来源正文及逐行diff。 | 超scope只建议，不自行改Plan/B面；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | Plan缺失/范围模糊标BLOCKED相关判断；原文件细节/模板见来源正文及逐行diff。 | Plan缺失/范围模糊标BLOCKED相关判断；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每文件对齐/漂移/理由及风险有证据；原文件细节/模板见来源正文及逐行diff。 | 每文件对齐/漂移/理由及风险有证据 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回implement/self-review原步骤；不跨阶段；原文件细节/模板见来源正文及逐行diff。 | 返回implement/self-review原步骤；不跨阶段；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S15 mj-agent-flow-self-review
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-self-review/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-self-review/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-self-review/SKILL.md`；部署 `.agents/skills/mj-agent-flow-self-review/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-self-review/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage11提交前自检；原文件细节/模板见来源正文及逐行diff。 | Stage11提交前自检 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | staged/实际指定diff、Plan、验证结果；原文件细节/模板见来源正文及逐行diff。 | staged/实际指定diff、Plan、验证结果 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读diff/docs；产12项+双段+commit草案；原文件细节/模板见来源正文及逐行diff。 | 只读diff/docs；产12项+双段+commit草案 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | context→scope-drift→双段→12项→5a-d反扫→message→风险；原文件细节/模板见来源正文及逐行diff。 | context→scope-drift→双段→12项→5a-d反扫→message→风险 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 自检不含git add/commit；B批记录缺失NO-GO；原文件细节/模板见来源正文及逐行diff。 | 自检不含git add/commit；B批记录缺失NO-GO；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 空staged不等于无问题；指定worktree差异要明示；原文件细节/模板见来源正文及逐行diff。 | 空staged不等于无问题；指定worktree差异要明示；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 12项和scope/反扫/证据齐，GO仅自检结论；原文件细节/模板见来源正文及逐行diff。 | 12项和scope/反扫/证据齐，GO仅自检结论 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，建议git-commit；不自动提交；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，建议git-commit；不自动提交；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S16 mj-agent-flow-verify
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-verify/SKILL.md`；投影参考 `.agents/skills/mj-agent-flow-verify/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-flow-verify/SKILL.md`；部署 `.agents/skills/mj-agent-flow-verify/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-flow-verify/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage10本地命令矩阵；原文件细节/模板见来源正文及逐行diff。 | Stage10本地命令矩阵 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 变更scope、依赖版本、授权的验证层次；原文件细节/模板见来源正文及逐行diff。 | 变更scope、依赖版本、授权的验证层次 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读代码并运行受控离线检查；live需批准；原文件细节/模板见来源正文及逐行diff。 | 读代码并运行受控离线检查；live需批准 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 范围→A/B/C矩阵→A→询B→获准B→不跑C→报告；原文件细节/模板见来源正文及逐行diff。 | 范围→A/B/C矩阵→A→询B→获准B→不跑C→报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | LevelB逐服务授权；C删除/生产不默认执行；原文件细节/模板见来源正文及逐行diff。 | LevelB逐服务授权；C删除/生产不默认执行；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 失败记录最小复现；缺工具UNMET；skip不算外部通过；原文件细节/模板见来源正文及逐行diff。 | 失败记录最小复现；缺工具UNMET；skip不算外部通过；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 命令/环境/exit/skip/未测逐项可核；原文件细节/模板见来源正文及逐行diff。 | 命令/环境/exit/skip/未测逐项可核 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage10结束，建议self-review；原文件细节/模板见来源正文及逐行diff。 | Stage10结束，建议self-review；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S17 mj-agent-git-branch
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-branch/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-branch/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-branch/SKILL.md`；部署 `.agents/skills/mj-agent-git-branch/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-branch/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage2选择类型与创建worktree分支；原文件细节/模板见来源正文及逐行diff。 | Stage2选择类型与创建worktree分支 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 任务类型、base、branch名、绝对worktree目标；原文件细节/模板见来源正文及逐行diff。 | 任务类型、base、branch名、绝对worktree目标 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读git/common-dir与已有worktree；获准才新worktree/ref；原文件细节/模板见来源正文及逐行diff。 | 读git/common-dir与已有worktree；获准才新worktree/ref | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | precheck→类型→命名→碰撞→worktree add→健康核对；原文件细节/模板见来源正文及逐行diff。 | precheck→类型→命名→碰撞→worktree add→健康核对 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | G1仅worktree add；目标/动作批准不含其他Git操作；原文件细节/模板见来源正文及逐行diff。 | G1仅worktree add；目标/动作批准不含其他Git操作；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 同名/dirty/漂移停点；不checkout-b、不自动修裸仓配置；原文件细节/模板见来源正文及逐行diff。 | 同名/dirty/漂移停点；不checkout-b、不自动修裸仓配置；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 目标worktree/ref/base正确，状态明确；原文件细节/模板见来源正文及逐行diff。 | 目标worktree/ref/base正确，状态明确 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 独立结束，commit仅建议；原文件细节/模板见来源正文及逐行diff。 | 独立结束，commit仅建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S18 mj-agent-git-check-merge
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-check-merge/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-check-merge/SKILL.md`；部署 `.agents/skills/mj-agent-git-check-merge/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-check-merge/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | Stage16技术合并就绪检查；原文件细节/模板见来源正文及逐行diff。 | Stage16技术合并就绪检查 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | PR、head/base、CI、reviews、描述、commits；原文件细节/模板见来源正文及逐行diff。 | PR、head/base、CI、reviews、描述、commits | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读gh/git；产4门控+1信息表；原文件细节/模板见来源正文及逐行diff。 | 只读gh/git；产4门控+1信息表 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | PR定位→获取数据→冲突/CI/review/描述/merge commit→报告；原文件细节/模板见来源正文及逐行diff。 | PR定位→获取数据→冲突/CI/review/描述/merge commit→报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 只读不merge；未知/pending不通过；原文件细节/模板见来源正文及逐行diff。 | 只读不merge；未知/pending不通过；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | API失败/UNKNOWN如实标记；不能推定无CI就是满足保护；原文件细节/模板见来源正文及逐行diff。 | API失败/UNKNOWN如实标记；不能推定无CI就是满足保护；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 已观测门控及未验证required-check状态分开；原文件细节/模板见来源正文及逐行diff。 | 已观测门控及未验证required-check状态分开 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner人工决策，不通知他人或自动收尾；原文件细节/模板见来源正文及逐行diff。 | 返回Owner人工决策，不通知他人或自动收尾；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S19 mj-agent-git-commit
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-commit/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-commit/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-commit/SKILL.md`；部署 `.agents/skills/mj-agent-git-commit/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-commit/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 暂存/提交/message/split；原文件细节/模板见来源正文及逐行diff。 | 暂存/提交/message/split | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | branch、diff、目标文件、敏感文件元数据、scope表；原文件细节/模板见来源正文及逐行diff。 | branch、diff、目标文件、敏感文件元数据、scope表 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读diff/status；批准后精确stage/commit；原文件细节/模板见来源正文及逐行diff。 | 读diff/status；批准后精确stage/commit | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | status→秘密/个人排除→分组→scope→拆分→message→授权执行；原文件细节/模板见来源正文及逐行diff。 | status→秘密/个人排除→分组→scope→拆分→message→授权执行 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | Owner stage/commit范围；禁止秘密；不all盲加；原文件细节/模板见来源正文及逐行diff。 | Owner stage/commit范围；禁止秘密；不all盲加；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | hook block停止；部分stage对账；失败不amend他人commit；原文件细节/模板见来源正文及逐行diff。 | hook block停止；部分stage对账；失败不amend他人commit；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 文件集合/message/branch-type符合且实际commit有SHA；原文件细节/模板见来源正文及逐行diff。 | 文件集合/message/branch-type符合且实际commit有SHA | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，push只建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，push只建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S20 mj-agent-git-delete
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-delete/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-delete/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-delete/SKILL.md`；部署 `.agents/skills/mj-agent-git-delete/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-delete/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 删worktree/branch/已合并清理；原文件细节/模板见来源正文及逐行diff。 | 删worktree/branch/已合并清理 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 分支tip、绝对路径、dirty、合并证据、双remote范围；原文件细节/模板见来源正文及逐行diff。 | 分支tip、绝对路径、dirty、合并证据、双remote范围 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读身份；获准后remove worktree→本地→可选双remote；原文件细节/模板见来源正文及逐行diff。 | 读身份；获准后remove worktree→本地→可选双remote | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 目标→fetch状态→范围→H1/H2/H3→顺序删除→摘要；原文件细节/模板见来源正文及逐行diff。 | 目标→fetch状态→范围→H1/H2/H3→顺序删除→摘要 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | main/develop拒绝；删除/force需具体批准与可用路线；原文件细节/模板见来源正文及逐行diff。 | main/develop拒绝；删除/force需具体批准与可用路线；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原每步失败不阻塞后续；H2确认origin包含tip后自动-D；没有明确重入身份复核。 | 部分完成先对账；-d失败不自动-D；残目录不递归清；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 逐目标已删/保留/未知状态，恢复tip及未提交备份说明；原文件细节/模板见来源正文及逐行diff。 | 逐目标已删/保留/未知状态，恢复tip及未提交备份说明 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage17子调用返回，不自动sync下一任务；原文件细节/模板见来源正文及逐行diff。 | Stage17子调用返回，不自动sync下一任务；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S21 mj-agent-git-issue
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-issue/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-issue/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-issue/SKILL.md`；部署 `.agents/skills/mj-agent-git-issue/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-issue/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 用8模板起草/创建GitHub Issue；原文件细节/模板见来源正文及逐行diff。 | 用8模板起草/创建GitHub Issue | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 需求、类型、urgency、template、title/body；原文件细节/模板见来源正文及逐行diff。 | 需求、类型、urgency、template、title/body | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读模板/需求；草案，批准后外部create；原文件细节/模板见来源正文及逐行diff。 | 读模板/需求；草案，批准后外部create | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 类型→完整模板→title→preview→确认发布→实际URL；原文件细节/模板见来源正文及逐行diff。 | 类型→完整模板→title→preview→确认发布→实际URL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 创建需明确授权，template硬停项不删；原文件细节/模板见来源正文及逐行diff。 | 创建需明确授权，template硬停项不删；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 缺模板/认证停对应发布；重复先检索避免重开；原文件细节/模板见来源正文及逐行diff。 | 缺模板/认证停对应发布；重复先检索避免重开；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 模板字段完整；实际创建才报告URL；原文件细节/模板见来源正文及逐行diff。 | 模板字段完整；实际创建才报告URL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，branch仅建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，branch仅建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S22 mj-agent-git-pr
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-pr/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-pr/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-pr/SKILL.md`；部署 `.agents/skills/mj-agent-git-pr/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-pr/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 按分支模板准备/创建PR；原文件细节/模板见来源正文及逐行diff。 | 按分支模板准备/创建PR | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | head/base、commits、diff、模板、验证、CHANGELOG；原文件细节/模板见来源正文及逐行diff。 | head/base、commits、diff、模板、验证、CHANGELOG | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读git与模板；body-file草案，获准gh create；原文件细节/模板见来源正文及逐行diff。 | 读git与模板；body-file草案，获准gh create | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 前置→模板→字段→自检→明确base/body-file→确认创建；原文件细节/模板见来源正文及逐行diff。 | 前置→模板→字段→自检→明确base/body-file→确认创建 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | Owner PR create；non-hotfix develop/hotfix main；不merge；原文件细节/模板见来源正文及逐行diff。 | Owner PR create；non-hotfix develop/hotfix main；不merge；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | dirty/缺push/CI信息未知分别处理，不代跑push；原文件细节/模板见来源正文及逐行diff。 | dirty/缺push/CI信息未知分别处理，不代跑push；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 模板/字段/base正确；实际创建有URL；原文件细节/模板见来源正文及逐行diff。 | 模板/字段/base正确；实际创建有URL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，check-merge只建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，check-merge只建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S23 mj-agent-git-push
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-push/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-push/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-push/SKILL.md`；部署 `.agents/skills/mj-agent-git-push/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-push/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 推送/推送前检查/双推；原文件细节/模板见来源正文及逐行diff。 | 推送/推送前检查/双推 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | branch、commit、lint/type/tests/docs/changelog状态、remotes；原文件细节/模板见来源正文及逐行diff。 | branch、commit、lint/type/tests/docs/changelog状态、remotes | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读8项检查；获准后gitee→origin push；原文件细节/模板见来源正文及逐行diff。 | 读8项检查；获准后gitee→origin push | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 八项pre-push→文档/日志→worktree→双推→状态；原文件细节/模板见来源正文及逐行diff。 | 八项pre-push→文档/日志→worktree→双推→状态 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | push需Owner；force-with-lease另核head与授权；原文件细节/模板见来源正文及逐行diff。 | push需Owner；force-with-lease另核head与授权；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 一端成功一端失败分别报；认证失败不显示token；原文件细节/模板见来源正文及逐行diff。 | 一端成功一端失败分别报；认证失败不显示token；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 两端SHA/失败端/未执行端分别确认；原文件细节/模板见来源正文及逐行diff。 | 两端SHA/失败端/未执行端分别确认 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，PR仅建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，PR仅建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S24 mj-agent-git-review-pr
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-review-pr/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-review-pr/SKILL.md`；部署 `.agents/skills/mj-agent-git-review-pr/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-review-pr/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 审别人PR架构/数据边界；原文件细节/模板见来源正文及逐行diff。 | 审别人PR架构/数据边界 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 他人PR URL/head、diff、branch、规范；原文件细节/模板见来源正文及逐行diff。 | 他人PR URL/head、diff、branch、规范 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读PR和实际文件；本地review草案；原文件细节/模板见来源正文及逐行diff。 | 只读PR和实际文件；本地review草案 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 定位→变更概览→F1-F3/D1-D9→草案→授权发布建议→人工决策；原文件细节/模板见来源正文及逐行diff。 | 定位→变更概览→F1-F3/D1-D9→草案→授权发布建议→人工决策 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | D3-D7保护审查；评论明确授权；merge人工；原文件细节/模板见来源正文及逐行diff。 | D3-D7保护审查；评论明确授权；merge人工；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | PR关闭/目标变更停；工具缺失不能伪造review；原文件细节/模板见来源正文及逐行diff。 | PR关闭/目标变更停；工具缺失不能伪造review；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每发现有文件/影响/依据，未测项清楚；原文件细节/模板见来源正文及逐行diff。 | 每发现有文件/影响/依据，未测项清楚 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 原Stage5人工双确认后由agent gh pr merge --delete-branch；本阶段Owner要求保留人工合并硬边界。 | 独立返回，check-merge建议；不修他人分支；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S25 mj-agent-git-sync
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-sync/SKILL.md`；投影参考 `.agents/skills/mj-agent-git-sync/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-git-sync/SKILL.md`；部署 `.agents/skills/mj-agent-git-sync/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-git-sync/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 开发期/热修回同步/同分支自更新；原文件细节/模板见来源正文及逐行diff。 | 开发期/热修回同步/同分支自更新 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | branch/base、remote状态、dirty、模式；原文件细节/模板见来源正文及逐行diff。 | branch/base、remote状态、dirty、模式 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读图谱；按模式merge目标ref，hotfix推送另批准；原文件细节/模板见来源正文及逐行diff。 | 读图谱；按模式merge目标ref，hotfix推送另批准 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | precheck→模式→fetch→差异→merge按意图解冲突→验证；原文件细节/模板见来源正文及逐行diff。 | precheck→模式→fetch→差异→merge按意图解冲突→验证 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 保持merge不用rebase；冲突/dirty/写目标核授权；原文件细节/模板见来源正文及逐行diff。 | 保持merge不用rebase；冲突/dirty/写目标核授权；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 冲突保留现场逐块按意图；无全树reset，重入核MERGE_HEAD；原文件细节/模板见来源正文及逐行diff。 | 冲突保留现场逐块按意图；无全树reset，重入核MERGE_HEAD；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 目标ref纳入，冲突清零且工作树一致；原文件细节/模板见来源正文及逐行diff。 | 目标ref纳入，冲突清零且工作树一致 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回原开发/Stage17调用者，不自动发布；原文件细节/模板见来源正文及逐行diff。 | 返回原开发/Stage17调用者，不自动发布；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S26 mj-agent-infra-app-start
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-start/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-app-start/SKILL.md`；部署 `.agents/skills/mj-agent-infra-app-start/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-start/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 有序启动本地dev runtime；原文件细节/模板见来源正文及逐行diff。 | 有序启动本地dev runtime | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 原Step0用Select-String直接读.env取provider。 | worktree、provider状态、runtime选择、已有端口/compose | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读脱敏前置与状态；获准起storage/runtime；原文件细节/模板见来源正文及逐行diff。 | 读脱敏前置与状态；获准起storage/runtime | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | cwd/provider→prereq→already-running→runtime→storage→live→launch→verify；原文件细节/模板见来源正文及逐行diff。 | cwd/provider→prereq→already-running→runtime→storage→live→launch→verify | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原slim HITL依赖Bash prompt执行拍板；ModeB假定Bash run_in_background及会话终止连带子进程。 | 缺凭据Owner终端；live单列授权；后台未验证不假造；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | already-running不重启；up成功live失败记部分完成不自动down；原文件细节/模板见来源正文及逐行diff。 | already-running不重启；up成功live失败记部分完成不自动down；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 根URL/容器状态/覆盖检查真实，未验证不填绿；原文件细节/模板见来源正文及逐行diff。 | 根URL/容器状态/覆盖检查真实，未验证不填绿 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage10子调用返回；probe/stop仅建议；原文件细节/模板见来源正文及逐行diff。 | Stage10子调用返回；probe/stop仅建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S27 mj-agent-infra-app-stop
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-stop/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-app-stop/SKILL.md`；部署 `.agents/skills/mj-agent-infra-app-stop/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-stop/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 非破坏停止app并保留数据；原文件细节/模板见来源正文及逐行diff。 | 非破坏停止app并保留数据 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | app-start身份、PID/start time/port、project/profile/-f；原文件细节/模板见来源正文及逐行diff。 | app-start身份、PID/start time/port、project/profile/-f | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读进程/容器；获准停精确进程树或Level1 down；原文件细节/模板见来源正文及逐行diff。 | 读进程/容器；获准停精确进程树或Level1 down | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 现状→无目标早退→多目标选择→身份核验停止→verify→销毁边界；原文件细节/模板见来源正文及逐行diff。 | 现状→无目标早退→多目标选择→身份核验停止→verify→销毁边界 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 只停已确认目标；删数据转teardown停点；原文件细节/模板见来源正文及逐行diff。 | 只停已确认目标；删数据转teardown停点；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原down超时60s后docker kill固定容器名；端口owner停止无明确PID重用防护。 | PID复用停止；超时不自动kill；部分停逐目标记录；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 目标确已停止、volume/image保留，其他监听不误杀；原文件细节/模板见来源正文及逐行diff。 | 目标确已停止、volume/image保留，其他监听不误杀 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回app-start/Stage17调用者或独立结束；原文件细节/模板见来源正文及逐行diff。 | 返回app-start/Stage17调用者或独立结束；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S28 mj-agent-infra-docker-compose
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-docker-compose/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-docker-compose/SKILL.md`；部署 `.agents/skills/mj-agent-infra-docker-compose/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-docker-compose/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 低层compose up/ps/logs/down；原文件细节/模板见来源正文及逐行diff。 | 低层compose up/ps/logs/down | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | cwd、profile、-f链、project、脱敏key状态；原文件细节/模板见来源正文及逐行diff。 | cwd、profile、-f链、project、脱敏key状态 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 原含compose config展开与docker exec psql检查；故障建议起另项目栈/kill端口占用。 | 读compose结构/状态；获准生命周期操作 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | cwd→precheck/network/env→profile→action→verify→报告；原文件细节/模板见来源正文及逐行diff。 | cwd→precheck/network/env→profile→action→verify→报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | prod/外部镜像/删卷保留停点；配置quiet不泄密；原文件细节/模板见来源正文及逐行diff。 | prod/外部镜像/删卷保留停点；配置quiet不泄密；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 故障先定位，不跨mj-system操作；删卷非默认恢复；原文件细节/模板见来源正文及逐行diff。 | 故障先定位，不跨mj-system操作；删卷非默认恢复；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 实际ps/health/URL按覆盖记录，memory无工具未测；原文件细节/模板见来源正文及逐行diff。 | 实际ps/health/URL按覆盖记录，memory无工具未测 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回app-start/verify，独立不进入部署；原文件细节/模板见来源正文及逐行diff。 | 返回app-start/verify，独立不进入部署；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S29 mj-agent-infra-env-setup
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-setup/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-env-setup/SKILL.md`；部署 `.agents/skills/mj-agent-infra-env-setup/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-setup/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 环境/依赖/凭据准备指导；原文件细节/模板见来源正文及逐行diff。 | 环境/依赖/凭据准备指导 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 工具版本、非秘密profile、Owner状态、锁定依赖；原文件细节/模板见来源正文及逐行diff。 | 工具版本、非秘密profile、Owner状态、锁定依赖 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 原MCP维护旧脚本15项SSH/biz/memory到OS env；应用与MCP分离约束保留。 | 读公开模板和脱敏状态；Owner解密/OS写；获准uv sync | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | prereq→Owner app/MCP分离维护→脱敏完整性→uv sync→offline/live分开；原文件细节/模板见来源正文及逐行diff。 | prereq→Owner app/MCP分离维护→脱敏完整性→uv sync→offline/live分开 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 口令/秘密不入agent；只6项目变量；P1工具未真实运行；原文件细节/模板见来源正文及逐行diff。 | 口令/秘密不入agent；只6项目变量；P1工具未真实运行；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 部分注入只键名对账；不自动重解密或改策略；原文件细节/模板见来源正文及逐行diff。 | 部分注入只键名对账；不自动重解密或改策略；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 原默认check被写为DB+LLM成功；源PS5.1前置不能代表P1的pwsh候选已支持。 | 步骤状态与实际覆盖分开，不以check证明LLM/MCP | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage8返回；app-start建议，不自动探针；原文件细节/模板见来源正文及逐行diff。 | Stage8返回；app-start建议，不自动探针；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S30 mj-agent-infra-env-teardown
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-teardown/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-env-teardown/SKILL.md`；部署 `.agents/skills/mj-agent-infra-env-teardown/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-teardown/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 明确重置/销毁dev资源；原文件细节/模板见来源正文及逐行diff。 | 明确重置/销毁dev资源 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | context/host/project/profile/-f、精确volume/image、level、备份；原文件细节/模板见来源正文及逐行diff。 | context/host/project/profile/-f、精确volume/image、level、备份 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读资源身份；获准Level1/2/3清理；原文件细节/模板见来源正文及逐行diff。 | 读资源身份；获准Level1/2/3清理 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | profile→资源清单→level→损失+批准→执行→逐项verify；原文件细节/模板见来源正文及逐行diff。 | profile→资源清单→level→损失+批准→执行→逐项verify | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | Level2/3硬批准；prod单独停；外部网络/他人资源禁止；原文件细节/模板见来源正文及逐行diff。 | Level2/3硬批准；prod单独停；外部网络/他人资源禁止；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原无.env/无容器卷可早退，Level3没有覆盖残留本地镜像；超时自动kill建议。 | 目标变化停；部分清理不重做成功项；busy不force；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | level目标逐项完成；残留和不可恢复数据诚实报告；原文件细节/模板见来源正文及逐行diff。 | level目标逐项完成；残留和不可恢复数据诚实报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回调用阶段，不自动up或新任务；原文件细节/模板见来源正文及逐行diff。 | 返回调用阶段，不自动up或新任务；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S31 mj-agent-infra-llm-endpoint-probe
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`；部署 `.agents/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | local-openai-compat兼容探针；原文件细节/模板见来源正文及逐行diff。 | local-openai-compat兼容探针 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | provider/模型配置状态、已授权endpoint、脱敏脚本；原文件细节/模板见来源正文及逐行diff。 | provider/模型配置状态、已授权endpoint、脱敏脚本 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读脚本与脱敏输出；获准4步live请求；原文件细节/模板见来源正文及逐行diff。 | 读脚本与脱敏输出；获准4步live请求 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | precheck→models/reachability→model id→1token chat→tool calling→verdict；原文件细节/模板见来源正文及逐行diff。 | precheck→models/reachability→model id→1token chat→tool calling→verdict | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | live明确授权；无秘密组curl；部署/SSH不承接；原文件细节/模板见来源正文及逐行diff。 | live明确授权；无秘密组curl；部署/SSH不承接；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | exit0/3/2/1分开；缺模型/工具能力不伪通过；原文件细节/模板见来源正文及逐行diff。 | exit0/3/2/1分开；缺模型/工具能力不伪通过；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 4步输出与toolcalling结论各有真实证据；原文件细节/模板见来源正文及逐行diff。 | 4步输出与toolcalling结论各有真实证据 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回app-start/Studio调用者；服务端修改只建议；原文件细节/模板见来源正文及逐行diff。 | 返回app-start/Studio调用者；服务端修改只建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S32 mj-agent-infra-storage-stack
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-storage-stack/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-storage-stack/SKILL.md`；部署 `.agents/skills/mj-agent-infra-storage-stack/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-storage-stack/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 自有memory/redis结构与维护指导；原文件细节/模板见来源正文及逐行diff。 | 自有memory/redis结构与维护指导 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | dev目标、源码/版本、授权memory接口、备份状态；原文件细节/模板见来源正文及逐行diff。 | dev目标、源码/版本、授权memory接口、备份状态 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 原schema/备份恢复提供直接psql/pg_dump/DROP；并含未经核实created_at与pg_dump --where。 | 读结构；只读已授权memory；备份恢复交Owner | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 选init/schema/backup/redis/trouble→证据→方案→返回；原文件细节/模板见来源正文及逐行diff。 | 选init/schema/backup/redis/trouble→证据→方案→返回 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 禁直接DB客户端；biz链路独立；restore/migration硬停；原文件细节/模板见来源正文及逐行diff。 | 禁直接DB客户端；biz链路独立；restore/migration硬停；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原init失败建议删卷重建、修改init脚本；缺工具/部分restore停点未显式。 | 无schema工具UNMET；恢复失败保留现场不DROP重试；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 结构解释有依据；未执行backup/restore明确缺依赖；原文件细节/模板见来源正文及逐行diff。 | 结构解释有依据；未执行backup/restore明确缺依赖 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage8子调用返回；compose/implement为建议；原文件细节/模板见来源正文及逐行diff。 | Stage8子调用返回；compose/implement为建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S33 mj-agent-infra-studio-probe
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-studio-probe/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-studio-probe/SKILL.md`；部署 `.agents/skills/mj-agent-infra-studio-probe/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-studio-probe/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | dev Studio H1/H2/H3/R1/R2走查；原文件细节/模板见来源正文及逐行diff。 | dev Studio H1/H2/H3/R1/R2走查 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | dev工具链/Studio、endpoint、授权、trace收集范围；原文件细节/模板见来源正文及逐行diff。 | dev工具链/Studio、endpoint、授权、trace收集范围 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读公共指南；获准UI请求及脱敏证据；原文件细节/模板见来源正文及逐行diff。 | 读公共指南；获准UI请求及脱敏证据 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | endpoint前置→Studio→H1表→H2趋势→H3top→R1拒绝→R2限量→报告；原文件细节/模板见来源正文及逐行diff。 | endpoint前置→Studio→H1表→H2趋势→H3top→R1拒绝→R2限量→报告 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | biz仅应用工具链；R1异常停；不得放宽runtime；原文件细节/模板见来源正文及逐行diff。 | biz仅应用工具链；R1异常停；不得放宽runtime；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 原端口占用建议kill，依赖冲突建议递归删.venv；红线失败需停止。 | trace失败未验证；部分完成不凑5/5；不强杀/删venv；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 每例轨迹/拒绝/限量有证据，未做项明确；原文件细节/模板见来源正文及逐行diff。 | 每例轨迹/拒绝/限量有证据，未做项明确 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | Stage10返回；仅起服请求转app-start；原文件细节/模板见来源正文及逐行diff。 | Stage10返回；仅起服请求转app-start；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S34 mj-agent-runtime-biz-catalog-sync
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md`；部署 `.agents/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | catalog镜像与脱敏快照漂移；原文件细节/模板见来源正文及逐行diff。 | catalog镜像与脱敏快照漂移 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | Owner背书快照、catalog、上游命名规范、依赖引用；原文件细节/模板见来源正文及逐行diff。 | Owner背书快照、catalog、上游命名规范、依赖引用 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读快照/catalog/skills/eval；仅propose差异；原文件细节/模板见来源正文及逐行diff。 | 读快照/catalog/skills/eval；仅propose差异 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | offline diff→分类→六处反扫→catalog/cross-update草案→impact→HITL；原文件细节/模板见来源正文及逐行diff。 | offline diff→分类→六处反扫→catalog/cross-update草案→impact→HITL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原propose→Owner→settings ask门直接Edit；保留领域审阅与保护枚举，不能把聊天批准解释为P1 hook解锁。 | biz-catalog-sync停点；批准不解hook；无快照不连库；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | SKIP_NO/STALE不是无漂移；目标hash变重提；未知部分写不覆盖；原文件细节/模板见来源正文及逐行diff。 | SKIP_NO/STALE不是无漂移；目标hash变重提；未知部分写不覆盖；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 漂移/影响/依赖/提案/未验证明确；原文件细节/模板见来源正文及逐行diff。 | 漂移/影响/依赖/提案/未验证明确 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner，runtime同伴仅建议；不改catalog本阶段；原文件细节/模板见来源正文及逐行diff。 | 返回Owner，runtime同伴仅建议；不改catalog本阶段；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S35 mj-agent-runtime-eval-baseline
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-eval-baseline/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-runtime-eval-baseline/SKILL.md`；部署 `.agents/skills/mj-agent-runtime-eval-baseline/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-eval-baseline/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | 为runtime改动设计EVAL基线；原文件细节/模板见来源正文及逐行diff。 | 为runtime改动设计EVAL基线 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 目标skill/prompt、模板、现有eval引用/fixtures；原文件细节/模板见来源正文及逐行diff。 | 目标skill/prompt、模板、现有eval引用/fixtures | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读目标/模板；产EVAL草案，批准后docs/evaluation；原文件细节/模板见来源正文及逐行diff。 | 读目标/模板；产EVAL草案，批准后docs/evaluation | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 读target→kind→反扫→dataset→judge→baseline/threshold→模板→impact→HITL；原文件细节/模板见来源正文及逐行diff。 | 读target→kind→反扫→dataset→judge→baseline/threshold→模板→impact→HITL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 只设计不跑EVAL、不改runtime；落盘需Owner；原文件细节/模板见来源正文及逐行diff。 | 只设计不跑EVAL、不改runtime；落盘需Owner；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 无实测baseline留null/TODO，不编指标；目标变化重评；原文件细节/模板见来源正文及逐行diff。 | 无实测baseline留null/TODO，不编指标；目标变化重评；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 8段草案/kind/dataset/judge/阈值与未测状态完整；原文件细节/模板见来源正文及逐行diff。 | 8段草案/kind/dataset/judge/阈值与未测状态完整 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回runtime调用者或Owner，不自动开issue/EVAL；原文件细节/模板见来源正文及逐行diff。 | 返回runtime调用者或Owner，不自动开issue/EVAL；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S36 mj-agent-runtime-prompt-version-bump
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-prompt-version-bump/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-runtime-prompt-version-bump/SKILL.md`；部署 `.agents/skills/mj-agent-runtime-prompt-version-bump/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-prompt-version-bump/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | system Prompt版本/正文改进提案；原文件细节/模板见来源正文及逐行diff。 | system Prompt版本/正文改进提案 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | system.md、version/eval、装配/skills/ADR引用；原文件细节/模板见来源正文及逐行diff。 | system.md、version/eval、装配/skills/ADR引用 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 只读prompt/依赖；propose version/body/frontmatter diff；原文件细节/模板见来源正文及逐行diff。 | 只读prompt/依赖；propose version/body/frontmatter diff | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 读取→body审计→反扫→数据边界sanity→diff/version→impact→HITL；原文件细节/模板见来源正文及逐行diff。 | 读取→body审计→反扫→数据边界sanity→diff/version→impact→HITL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原propose→Owner→settings ask门直接Edit；保留领域审阅与保护枚举，不能把聊天批准解释为P1 hook解锁。 | prompt-version-or-body-change；sanity失败拒绝；批准不解锁；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 目标变化旧diff作废；部分apply对账无盲覆；拒绝不写；原文件细节/模板见来源正文及逐行diff。 | 目标变化旧diff作废；部分apply对账无盲覆；拒绝不写；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | diff/版本/EVAL/边界/影响齐，批准与执行各有状态；原文件细节/模板见来源正文及逐行diff。 | diff/版本/EVAL/边界/影响齐，批准与执行各有状态 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner或implement；self-review仅建议；原文件细节/模板见来源正文及逐行diff。 | 返回Owner或implement；self-review仅建议；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

## S37 mj-agent-runtime-skill-doc-improve
来源 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-skill-doc-improve/SKILL.md`；投影参考 `无（非能力缺失）`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-runtime-skill-doc-improve/SKILL.md`；部署 `.agents/skills/mj-agent-runtime-skill-doc-improve/SKILL.md`。恢复：20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-runtime-skill-doc-improve/SKILL.md; current candidate bytes only in this uncommitted worktree。
| 维度 | 来源语义 | 候选语义 | 处置/依据 |
|---|---|---|---|
| 触发 | runtime SKILL五段式正文改进；原文件细节/模板见来源正文及逐行diff。 | runtime SKILL五段式正文改进 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 输入 | 目标13字段/五段式、loader、引用/EVAL；原文件细节/模板见来源正文及逐行diff。 | 目标13字段/五段式、loader、引用/EVAL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 读写目标 | 读runtime/agent/prompt/docs；propose正文及元数据diff；原文件细节/模板见来源正文及逐行diff。 | 读runtime/agent/prompt/docs；propose正文及元数据diff | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 顺序 | 读target→五段审计→反扫→diff/version/eval→impact→HITL；原文件细节/模板见来源正文及逐行diff。 | 读target→五段审计→反扫→diff/version/eval→impact→HITL | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 授权 | 原propose→Owner→settings ask门直接Edit；保留领域审阅与保护枚举，不能把聊天批准解释为P1 hook解锁。 | runtime-skill-content-change；领域+Prompt评审，批准不解锁；P1 hard block，批准不解hook；无执行路线返回BLOCKED_EXECUTION_ROUTE。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 异常恢复 | 缺段/冲突逐项报告；目标变重审；不自动写src；原文件细节/模板见来源正文及逐行diff。 | 缺段/冲突逐项报告；目标变重审；不自动写src；并按共用说明做身份复核/部分完成对账/只续未完成项。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 完成判据 | 五段/反扫/diff/EVAL/风险可审阅，未执行明确；原文件细节/模板见来源正文及逐行diff。 | 五段/反扫/diff/EVAL/风险可审阅，未执行明确 | 保留（必要处原生化）；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |
| 交接返回 | 返回Owner或implement原步骤；不自动commit；原文件细节/模板见来源正文及逐行diff。 | 返回Owner或implement原步骤；不自动commit；独立/委派/建议三态与调用者返回阶段明确，不自动发布。 | 保留工程语义；改写执行边界；原始源完整正文 + 迁移计划§4.4/AC-02；用户P2约束；共享执行边界对应段 |

