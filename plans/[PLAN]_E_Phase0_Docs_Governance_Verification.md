---
type: plan
summary: 验证 Phase 0 文档治理 v1.0 交付物端到端可用——loader 剥离、运行时无泄露、A-rules 可执行
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-27
state: draft
---

# PLAN E — Phase 0 文档治理 v1.0 验证

## Context — 为什么现在做

[[../docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|mj-agent 文档治理框架 v1.1（archive）]] 及配套交付（4 份模板、9 份 ADR、`docs/INDEX.md`、src 源码改造、PR 模板补丁）已经全部落地到 `phase0-next-plans/` 这个 worktree。但两类事实尚未被验证：

1. **运行时行为**：loader 剥离 frontmatter 是否真的生效？`langgraph dev` 起的 agent 是否仍然正常响应？
2. **治理可执行性**：PR 模板里的 A1-A10 清单、SKILL/PROMPT/CONTRACT 模板，真正用起来是否顺手？有没有默认值歧义、路径错位、依赖缺失？

本 PLAN 定义一个 **最小端到端验证**——跑通就说明 Phase 0 文档治理体系可以交付给团队；跑不通就立刻暴露问题让我们在合入 `develop` 前修。不覆盖 Phase 0.5/1/2 的能力（见"明确不做"）。

## 决策前提（已确认）

| 决策 | 选择 | 理由 |
| --- | --- | --- |
| 验证是否跨 worktree | **仅在 `phase0-next-plans` 内验证** | 不污染 `develop/` 的 `.venv` 与运行时状态；合入 develop 前先在此 worktree 自证 |
| 是否安装 python-frontmatter | **必装**（`uv sync` 后自动） | 新 loader 硬依赖，不装就不起 |
| 是否跑 `langgraph dev` | **跑** | 最终正向验证——LLM 真实响应；如跳过，frontmatter 泄露可能仍被漏掉 |
| 是否临时造一个 dummy skill 验证 A7 | **造** | 唯一能在 Phase 0 阶段实证 SKILL 路径约束的方式 |

## 验证矩阵

| 编号 | 验证项 | 手段 | Pass 判据 |
| --- | --- | --- | --- |
| V1 | 依赖安装成功 | `uv sync` | `uv.lock` 更新含 `python-frontmatter`；无错误 |
| V2 | Ruff 通过 | `uv run ruff check` | Exit 0；无新警告 |
| V3 | mypy 通过 | `uv run mypy src/mj_agent` | Exit 0 |
| V4 | `load_skill` body 无 frontmatter 泄露 | `uv run python -c "from mj_agent.skills import load_skill; b=load_skill('query-writing'); assert not b.startswith('---'), b[:80]; print('skill body', len(b), 'chars')"` | 断言不触发，输出字符数 > 500 |
| V5 | `load_prompt` body 无 frontmatter 泄露 | `uv run python -c "from mj_agent.prompts import load_prompt; b=load_prompt('system'); assert not b.startswith('---'), b[:80]; print('prompt body', len(b), 'chars')"` | 断言不触发，输出字符数 > 500 |
| V6 | `load_skill_meta` 返回 frontmatter dict | `uv run python -c "from mj_agent.skills import load_skill_meta; m=load_skill_meta('query-writing'); assert m['type']=='skill' and m['version']=='v0.1' and m['state']=='active'; print('skill meta OK', list(m))"` | 断言不触发 |
| V7 | `load_prompt_meta` 返回 frontmatter dict | `uv run python -c "from mj_agent.prompts import load_prompt_meta; m=load_prompt_meta('system'); assert m['type']=='prompt' and m['model_binding']=='deepseek-v3'; print('prompt meta OK', list(m))"` | 断言不触发 |
| V8 | 单元/集成测试通过 | `uv run pytest tests/unit tests/integration` | Exit 0（已有套件无回归） |
| V9 | `langgraph dev` 能启动 | `uv run langgraph dev`（2 分钟观察） | Studio URL 开启；导入 `make_graph` 不报错；无 frontmatter 相关 Traceback |
| V10 | `langgraph dev` 中 agent 响应正常 | 在 Studio 发送："mj-system 里 biz_dws 有哪些日粒度表？" | agent 调 `list_biz_tables`；响应不含 "type: skill"/"owner:" 等元数据字样 |
| V11 | A7 可执行（dummy skill 实证） | 按 §3 步骤造一个 `demo-noop` skill，跑 PR 模板清单 | `feature.md` 清单所有 A 项均可勾选 |
| V12 | Wikilink 目标存在（A4 手工扫描） | `grep -r '\[\[' docs/ src/mj_agent/skills src/mj_agent/prompts \| awk -F'\[\[' '{for(i=2;i<=NF;i++)print $i}' \| awk -F'\]\]' '{print $1}' \| sort -u` 然后人工扫读 | 所有引用的文档/段落都存在 |
| V13 | CLAUDE.md 段落能被 Claude 读到并执行 | 在 Claude Code 里问："项目的文档治理入口在哪？" | Claude 引用 `docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`（PLAN E 撰写时的当时版本；Phase 0.5 后等价语义见 v2.0 trio）和 `docs/INDEX.md` |

## 执行步骤

### 1. 环境准备（一次）

```bash
cd "D:/workspace/10-software-project/projects/mj-agent/documentation/phase0-next-plans"
uv sync                                          # V1
uv run ruff check                                # V2
uv run mypy src/mj_agent                         # V3
```

任一失败 → 停在此步排错，**不继续后面**。

### 2. Loader 剥离验证（<1 分钟）

```bash
uv run python -c "from mj_agent.skills import load_skill; b=load_skill('query-writing'); assert not b.startswith('---'), b[:80]; print('V4 skill body', len(b), 'chars')"
uv run python -c "from mj_agent.prompts import load_prompt; b=load_prompt('system'); assert not b.startswith('---'), b[:80]; print('V5 prompt body', len(b), 'chars')"
uv run python -c "from mj_agent.skills import load_skill_meta; m=load_skill_meta('query-writing'); assert m['type']=='skill' and m['version']=='v0.1' and m['state']=='active'; print('V6 skill meta OK', list(m))"
uv run python -c "from mj_agent.prompts import load_prompt_meta; m=load_prompt_meta('system'); assert m['type']=='prompt' and m['model_binding']=='deepseek-v3'; print('V7 prompt meta OK', list(m))"
```

### 3. A7 实证：造一个 dummy skill，再删掉

**目的**：走一遍完整的"新 skill 上线流程"，证明 TEMPLATE_SKILL + A7 清单可执行。不改动 agent 代码，即不 import 这个 skill。

```bash
mkdir -p src/mj_agent/skills/demo-noop
cp docs/_templates/TEMPLATE_SKILL.md src/mj_agent/skills/demo-noop/SKILL.md
```

在 `src/mj_agent/skills/demo-noop/SKILL.md` 填入最小合法 frontmatter：

```yaml
---
type: skill
domain: SKILL
summary: 仅用于 PLAN E 验证 A7 合法性的占位 skill，验证完即删
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: draft
version: v0.0
activation:
  when_to_use: 不触发（验证占位）
  when_not_to_use: 任何生产路径
tool_dependencies: []
related_prompts: []
---
```

然后走一遍 `feature.md` PR 模板清单：

- [ ] A1 路径 `src/mj_agent/skills/demo-noop/SKILL.md` 合法 ✓
- [ ] A2 frontmatter 必填字段齐全 ✓
- [ ] A3 `state: draft` 合法 ✓
- [ ] A7 目录存在且与文档身份一致 ✓

确认清单全绿后**立即清理**：

```bash
rm -rf src/mj_agent/skills/demo-noop
```

### 4. 运行时端到端（`langgraph dev`）

需要 `ARK_API_KEY` 已配置（`.env`）。

```bash
uv run langgraph dev
```

打开 Studio URL，在对话框输入：

> mj-system 里 biz_dws 有哪些日粒度表？

观察：

1. Agent 不应在响应里出现任何 `type:`、`owner:`、`created:`、`summary:` 字样——这些是 frontmatter 字段名，出现即证明 loader 剥离失败
2. Agent 应当调用 `list_biz_tables()` 工具（可在 Studio 右侧 trace 面板看到）
3. 响应里的 SQL 应当仅使用 `biz_dws.*` 前缀

### 5. Wikilink 存在性扫描（V12）

```bash
grep -rh '\[\[' docs src/mj_agent/skills src/mj_agent/prompts | \
  grep -oP '\[\[\K[^\]]+' | sort -u
```

人工扫读输出：每一条 `[[...]]` 都应对应一个已存在的文件名（排除 `#` 开头的段内锚点和本身就是示例的 `[[SKILL]_Xxx]]` 占位）。

### 6. CLAUDE.md 可读性验证（V13）

在 Claude Code 里打开本 worktree 作为工作目录，新起一次会话，问：

> 这个仓库的文档治理入口在哪？

Claude 应当引用 `docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`（PLAN E 撰写时为 active；Phase 0.5 promote 后已归档，等价语义现由 v2.0 trio 承载）和 `docs/INDEX.md`。如果它引用其他文件或说"没找到"，说明 CLAUDE.md 的 Documentation 段落要再精简或加粗。

## Exit 判据

所有 V1-V13 Pass → Phase 0 文档治理 v1.0 视为**交付就绪**，可合入 `develop`。

任意 Pass 失败 → 归入下列分类处理：

| 失败位置 | 对应修复 |
| --- | --- |
| V1-V3 | 依赖/类型问题；最可能是 `python-frontmatter` 版本或 mypy 对 `frontmatter` 无 stubs |
| V4-V7 | loader 改造缺陷；修 `src/mj_agent/{skills,prompts}/__init__.py` |
| V8 | 既有测试套件对 loader 行为有假设；检查 `tests/unit/test_prompt*` 类文件 |
| V9-V10 | 运行时污染；如 V9 通过但 V10 失败，说明 frontmatter 没泄露但别处行为有回归 |
| V11 | TEMPLATE_SKILL 或 PR 模板清单不可执行；修模板 |
| V12 | INDEX.md 或 STANDARD 有失效链接；修链接 |
| V13 | CLAUDE.md 文档段落不够显眼或措辞模糊；重写 |

## 明确不做（Phase 0.5+ 再议）

- 自动校验器脚本（A1-A10 的 CI 自动化）——Phase 2
- `[EVAL]` 类型的首份文档——Phase 2
- `[RUNBOOK]` 模板与 `[GUIDE]_Add_A_New_Skill`——Phase 0.5
- `[CONTRACT]_Tool_SQLExecute_v1.0.md`——Phase 0.5（等 guardrail 接口稳定）
- ADR 010/011（biz schema 三层同步）的成文——Phase 0.5
- 从 `src/mj_agent/skills/*/SKILL.md` 生成 `docs/design/skills/INDEX.md` 的脚本——Phase 1

## 合入 `develop` 的后续动作（本 PLAN 不覆盖）

V1-V13 全绿后，`phase0-next-plans` 的内容需要合入 `develop`。建议一个独立的 PR（feature 类型），标题示例：

> feat(docs): adopt MJ-Agent Docs Framework v1.0 + 7 foundational ADRs + in-source canonical governance

PR 描述应当：
- 引用本 PLAN E 的验证结果（贴 V4/V5/V10 的输出）
- 列出全部 15 份新建/修改的文档文件
- 列出 4 份修改的源码/配置文件（loader + SKILL.md + system.md + pyproject.toml + CLAUDE.md + 7 PR 模板）
- 在 CHANGELOG.md 的 `[Unreleased]` 区块登记 `docs: introduce v1.0 governance framework`

具体 PR 动作不属于本 PLAN 的验证范围，由合入者执行。
