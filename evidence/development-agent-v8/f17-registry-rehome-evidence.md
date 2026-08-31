---
type: evidence
summary: >-
  F17（issue #522）registry re-home —— 把 V12 `Cross-Carrier-Structure` 与 V13
  `Codex-Enforcement-Drift` 的 `policies/ci-gates.md` §4.1.1 五要素观察期注册表，自
  `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.8/§5.9 迁到新建的合并 M-FU 工件
  `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.1/§2.2。动因 = ADR-039 第 11 条与该 plan
  §5.12 规定 PR-G 把它翻 `completed`，**PR-G 之后**才动作的消费者会引用一份已退休的记录
  （同 #403 失效模式）。**零 posture / 零执行体 / 零阈值 delta** ⇒ 按 #444 判例不需
  `ci-blocking-gate-toggle` 拍板。kernel plan §5.8/§5.9 **保留标题 + 开头交付散文 + 指针存根**，
  因其**编号是活体引用目标**（`ci.yml` 两个 step 名内嵌且自带「Do NOT rename this step」；
  `sdd/adapters/codex-enforcement.yml` 有 3 处 `plan SS5.9`，而该 typed source 的字节即 lock
  输入、不可为修引用而编辑）。随迁更正三处**已知为错**的陈述：F20 的钉线恢复面是**两处**不是
  一处（`c485f8d` 的 commit message 自述 "TWO pre-existing real-tree pins"）、四处「V12 行也写着」
  属**误归属**、以及「两 step 相隔约 1 秒」实为拿 `completed_at` 比 `started_at`。⚠ 三个
  `policy_ref` 零字节触达，经显式 sha 绊线核验 —— `task0_freeze.py --check` 已在 `AGENTS.md`
  上饱和，**不可**充当该绊线。分析与实测由 Claude Code 执行、方案由 Owner 拍板。
owner: ranzuozhou
created: 2026-08-31
updated: 2026-08-31
state: active
track: agent
---

# Registry Re-home — V12 / V13 观察期注册表（F17 / issue #522）

> 交付物 = `plans/[PLAN]_m-fu-v12-v13-gate-observation.md`（新建合并 M-FU 注册工件）。
> 上游 = Epic [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499) follow-up 表 **F17**。
> 本单元**不属** 18-PR 序列编号；plan §5.1 的 OBSERVATION 行只排除 "no active implementation
> goal"，治理搬迁不是实现。顺序约束 = **必须早于 PR-G**。

## 0. 入场核验（实测）

| 项 | 值 |
|---|---|
| 入场 base | develop `fb7ae7d39516392c6ac8605a06bebd2d44a146e9`（local = origin = gitee 三方一致） |
| 前序单元 | PR-D1b [#520](https://github.com/MJ-AgentLab/mj-agent/pull/520) MERGED，head `029d1e5d…`，`2026-08-28T09:40:38Z` |
| D1b ledger | [#499 comment 5451144519](https://github.com/MJ-AgentLab/mj-agent/issues/499#issuecomment-5451144519)：`rstrip("\n")` 后 **31161 B**，SHA-256 `b3b5ad50b196e46b467da7dee23e7c6121ece87c65879ec8810a37155173f3e6` 逐字节吻合，`'\r\n' not in body`，反引号 **344**，**18 records 全终态**（stage 0-17 连续、必填字段零缺失） |
| task0 | `CONTROLLED_SURFACE_CHANGED` / **rc 1**，identity `3bb781e2b184cfff3d8f34c6403fdd14da825c7854f981257be832a577aa0fac`，hard-frozen 58/58 —— **预期授权态，非 rc 0** |
| Epic / EVAL backlog | #499 OPEN · #504 OPEN |
| worktree | 入场 2（`.bare` + `develop`），本单元后 3 |

⚠ 入场时「无 open PR」，但 **2026-08-31 复核时出现 dependabot PR [#521](https://github.com/MJ-AgentLab/mj-agent/pull/521)**
（`infra(deps): bump python …`，非本 goal）。它对本单元的意义见 §2 —— 它贡献了 V13 计数腿的**第一个可计数观测**。

## 1. 交付面（Gate 1 批准的 exact scope）

| 文件 | 动作 |
|---|---|
| `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` | **新建** —— 合并 M-FU 注册工件，§1-§10 |
| `plans/[PLAN]_codex_cross_carrier_kernel.md` | §5.8/§5.9 表 + 注册载体声明段 → 指针存根；`:62` arity 修复；frontmatter `updated` |
| `sdd/gates.md` | V12/V13 两行共 8 处替换 + 升版三件套（`0.14`→`0.15` / `updated` / v0.15 changelog 条目） |
| `policies/ci-gates.md` | 仅 `:139` / `:293` 两处 arity 转义（**`:264` 有意不改** —— blockquote 非表格行） |
| `evidence/development-agent-v8/f17-registry-rehome-evidence.md` | **新建** —— 本文件 |

**有意不碰**：`.github/workflows/ci.yml`（V12/V13 step 名 = §4.1.1 gate 标识三元组第三腿，文件内自带
两处「Do NOT rename this step」）· `sdd/adapters/codex-enforcement.yml` · 三个 `policy_ref` ·
任何生成产物 · 任何 `src/mj_agent/**` · 任何测试。

## 2. 观察期实况（实测，时点 2026-08-31T01:13Z）

| 项 | V12 | V13 |
|---|---|---|
| 日历腿到期 | 2026-09-10 | **2026-09-11** |
| 计数腿起点 | 锚上首次真实 CI 之后 | PR-D1b merge `fb7ae7d` 之后 |
| 快照时可计数 streak | —— | **1** |

**V13 计数腿的第一个可计数观测（本单元实测）**：

```text
head        d201538e  (branch dependabot/docker/docker/develop/python-7ce4b6d, PR #521)
run         33346811871   event=pull_request   run_started_at 2026-08-31T01:11:07Z
job         99352366505
step #42    V12 …   started_at 2026-08-31T01:11:42Z -> completed_at 01:11:42Z
step #43    V13 …   started_at 2026-08-31T01:11:42Z -> completed_at 01:11:43Z
stdout(V13) OK: projection in sync (surface=enforcement, 18 skills, lock consistent)
            EXECUTED_CLEAN
```

⚠ 该 head SHA 只产生 **1 次** run（`dependabot/*` 不在 `ci.yml` 的 push 过滤器内）——
**这是「成对是可能不是保证」的第一个实例**，也直接证明**不得**用「run 数 ÷ 2」反推观测数。

⚠ **实操句柄（新事实）**：job 日志里的 step 分组行按**命令**标注，不是按 step 名 ——
形如 `##[group]Run uv run python scripts/sdd/agents_sync.py --check --surface enforcement`。
注册表要求的「按 step 切分日志」在实现时须按此锚定；按 step **名** grep 会零命中。

## 3. 三处随迁更正（各附可复跑判据）

### 3.1 F20 的钉线恢复面是**两处**，不是一处

迁移前 plan §5.9 与 `sdd/gates.md` V13 行都写「F20 要恢复的是**一处**调用点，不是两处」。**为假。**

```bash
git grep -n 'sync_main(\["--check"\], repo_root=REPO_ROOT)' 70a9db4 -- tests/
# → 70a9db4:tests/unit/test_agents_sync.py:1847
# → 70a9db4:tests/unit/test_v2_engine.py:564          （2 处）
git grep -n 'sync_main(\["--check"\], repo_root=REPO_ROOT)' fb7ae7d -- tests/ ; echo "rc=$?"
# → （无输出）rc=1                                     （0 处 —— 两处都被收窄）
git log -1 --format=%B c485f8d | grep -A 4 "real-tree pin"
# → TWO pre-existing real-tree pins ran bare --check (surface=all) inside the
#   BLOCKING Tests step, ... Both are now scoped to the two blocking surfaces; PR-D2
#   restores the unscoped call together with its ci-blocking-gate-toggle record.
#   (The review found one; the second came from an author re-sweep.)
```

**要恢复的两处**：`tests/unit/test_agents_sync.py::test_real_tree_projection_in_sync` 与
`tests/unit/test_v2_engine.py::test_real_tree_now_takes_the_v2_paths`。

**误判成因**：D1b 正确地发现同文件内的 `test_real_tree_mcp_projection_in_sync` **本来就是**
mcp-scoped、不在恢复面内，却据此把 D1a 的「两处」改判为「一处」—— 漏掉了第二处其实在**另一个文件**
`test_v2_engine.py` 里。D1a 的原始计数是对的。

⚠ **后果**：不修则 PR-D2 按 F20 只恢复两处钉线中的一处，enforcement 面的 envelope 级断言
（`#499-F22`）继续没有 blocking 兜底。

### 3.2 「V12 行也写着那句假陈述」属误归属

```bash
uv run --frozen --no-sync python -c "
l64 = open('sdd/gates.md', encoding='utf-8').read().split(chr(10))[63]
for t in ('届时','才到期','已在闭合记录','日历腿到期时'): print(t, l64.count(t))"
# → 届时 0 / 才到期 0 / 已在闭合记录 0 / 日历腿到期时 0
grep -rn "日历腿到期时" --include=*.md .
# → 只出现在 4 处「转述」里，从不作为源文本
```

可证伪子句「届时注册表将位于**已闭合的项目记录**中」**只存在于** kernel plan §5.8 的注册载体声明段
（迁移前的 `:1377`）。`sdd/gates.md:64` bullet (3) 是丢掉了该子句的截断版，其两个合取项
（「PR-G 会把 plan 翻 `completed`」「日历腿最早 2026-09-10 到期」）与结论各自为真 —— 至多是把日历腿
当成理由的**非因果推论**，不是假陈述。

四处误归属：`sdd/gates.md:65` · `plan:1414` · `evidence/…d1b:52` · `:529`。本单元更正前两处
（活体注册面）；**两个 evidence 文件不改** —— 历史执行账本，仓内惯例不回改，更正记在本文件。

### 3.3 「两个 step 相隔约 1 秒」是字段错配

```bash
gh api repos/MJ-AgentLab/mj-agent/actions/jobs/98762485194 \
  --jq '.steps[] | select(.number==42 or .number==43) | "\(.number) \(.started_at) -> \(.completed_at)"'
# → 42 2026-08-28T05:21:57Z -> 2026-08-28T05:21:57Z
# → 43 2026-08-28T05:21:57Z -> 2026-08-28T05:21:58Z
```

两 step 的 `started_at` **同为** `05:21:57Z`；原记的「1 秒」是拿 V13 的 `completed_at` 比 V12 的
`started_at`。API 粒度为 1 秒，观察不到亚秒间隔。**须保留的操作性告诫不变**：streak 度量必须按 step
切分日志（5 个 token 里 4 个与 V12 共用字面量）。

### 3.4 一并按可复跑谓词重写、不再转抄的陈旧数字

- 「本 Epic 至今 3 个 merge commit」—— 机制正确、计数陈旧（Epic 已产生 15 个 PR merge）。新工件 §3.3
  改写为**锚在 `ci.yml` workflow 上**的谓词而非计数。

  ⚠ **Stage 11 自查抓到本单元自己诱发的一处缺陷并已修，此处如实记录成因**：初稿沿用了迁入前的裸
  `.../actions/runs?head_sha=…` + `--jq .total_count`，**并把它推广成「本 Epic 每个 merge commit
  上均已实测为 0」的全称命题**。实测该全称为假：`fb7ae7d` 得 **3**、`33dd984` 得 **6**
  （19 个 merge commit 中 2 个），成因是 Dependabot 的 `weekly / monday / 09:00 Asia/Shanghai`
  （= 01:00 UTC）+ `target-branch: develop` 定时任务，其 `dynamic` run 被归属到当时的 develop 头 SHA；
  `33dd984` 跨两个周一 tick 故得 6。收窄到 `ci.yml` 后 **19 个全部为 0**。

  ⚠ **成因判定（经独立复核，推翻了一个更省事的解释）**：这**不是**「当时测对了、后来变陈旧」——
  `33dd984` 自 **2026-08-17** 起就已为假，比本单元实施早两周，故本 session 任一时刻做全量复扫都
  不可能得到全 0；且本单元分支创建于 `01:40:33Z`，比那批 Dependabot run 落地**晚 30 分钟**，
  §4 自报的快照时点 `01:13Z` 也已在其后。真正的成因是**把一个按 SHA 钉死时安全的谓词，
  在未测量的情况下推广成了全称命题** —— C2 与 D1b 两个 ledger 都是钉死 SHA 使用的，其记录值
  至今仍复现为 0，**它们没有错，也没有被继承错**。判据「谓词须能重算出自己记录的值」这次抓的是我。
- 「自 `c485f8d` 起 ci.yml 再无任何 run」—— 已不成立（`029d1e5` 上有 2 次）。新工件 §4 把**测量**与
  **自排除推理**分开写，结论（计数腿起点后的 streak）不受影响。

## 4. 护栏核验：三个 `policy_ref` 零字节触达

⚠ **`task0_freeze.py --check` 不可充当本护栏的检测器** —— 它已在 `AGENTS.md` 上**饱和**
（PR-C1 与 PR-D1a 两处授权 hunk 用尽，`CONTROLLED_SURFACE_CHANGED` 恒真），对**新增**编辑无鉴别力。
故本单元用显式 sha 绊线（diff 前后各跑一次，值须逐字相同）：

> ⚠ **下表全部四个文件哈希都是「原始字节 **CRLF→LF 归一化后** 的 SHA-256」** —— 三个 `.md`
> 在本仓工作树上确实含 CRLF，直接对 raw bytes 取 sha 会**三行全部对不上**，从而误判护栏已触发。
> 可复跑：
> `uv run --frozen --no-sync python -c "import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest())" <path>`

| 对象 | 值（diff 前后相同） |
|---|---|
| `AGENTS.md` | `f6b32d39f0549c780e4389effbd876462498118e25949ec726ae638f9931586f` |
| `policies/ai-agent.md` | `c4f3e98af12625e555b32997df31439213212abbad4020dc204b2cbfe5055849` |
| `policies/git-branching.md` | `c671e209a549636ef68ea4baa6b1e6aea692d127955f6cd48a9ba46622aad506` |
| `sdd/adapters/codex-enforcement.yml` | `2dc524960b54424c4e97acc631d16f854c5b3c6cfe1895b1da809790acf4bb9e` |
| lock `policy_refs_sha256`（2 条目，1 个 distinct 值） | `a030fa8b26f2f7019c646f1be223e2430f0b503bd771a9d4e10114140fde9a3a` |

**第四个不可碰面**：`sdd/adapters/codex-enforcement.yml` 本身 —— 它不是 `policy_ref`，但其**字节即
lock 输入**，且它有 3 处 `plan SS5.9` 引用。这正是 kernel plan §5.8/§5.9 **编号必须保留**的硬理由：
若删节或 renumber，修引用就得编辑 typed source，那会在保护 V13 epoch 的 PR 上重置该 epoch。

## 5. 验证结果

见 §6 命令矩阵。核心断言：

1. **渲染断言 delta = 0**（本单元特有风险：改的是高密度 CJK 表格 cell，表格 arity 检查对 emphasis
   泄漏**全盲**）。方法 = 整文件 CommonMark 渲染（`markdown_it`）→ 剔除 `<pre>` 与 `<code>` →
   数字面 `*` → 与 base 比。
   ⚠ **不得逐行渲染**：`sdd/gates.md` 的每条 changelog 条目是跨行 blockquote 内的**单个** `*…*`
   斜体块，逐行法会把基线严重误报。
   ⚠ 本单元自测基线 `sdd/gates.md` = **7**；Stage 3 扫描的一个镜头报 9 —— 口径差异（剥离 `<pre>`
   与否）。**因 AC 判的是 delta 而非绝对值，此处以本单元自己的方法为准并全程一致使用。**
2. **表格 arity**：三处既存违规修复后全仓在范围内文件 **0 违规**；`policies/ci-gates.md:264` 有意保留
   裸竖线（blockquote 非表格行，转义无必要）。
3. **§6.1 可复跑推导**：34 行命中（与 base 相同），V12/V13 两行仍以连字符形命中 —— 该正则**只读**
   第 1、2 列，看不见第 4 列的载体指针，故 re-home 对它**机器不可见**（合并审查是唯一兜底）。

## 6. 验证命令矩阵

见 PR body 与 Stage 17 ledger 的逐条原始输出。

## 7. 本单元明确**未**证明的事

1. **未**证明新工件被任何 gate 校验其**内容**。⚠ 措辞须精确：实测有 **4 个 CI 挂载的执行体**读
   `plans/**` —— `scripts/check_frontmatter.py`（**blocking**）· `scripts/find_old_completed_plans.py` ·
   `scripts/sdd/check_archived_references.py --all` · `scripts/find_stale_docs.py` —— 但四者分别只校验
   frontmatter schema / completed-GC 候选 / `archive/` 路径引用 / 重命名与删除的反引号路径，
   **与 §4.1.1 五要素、章节指针、token 口径全部正交**。故「§4.1.1 五要素齐全、pickaxe 判据可复跑、
   token 口径正确」**全靠本文件的断言与合并审查**。
   （早先草稿写「全仓只有 `check_frontmatter.py` 读 `plans/**`」—— **为假**，Stage 11 实测更正。）
2. **未**证明 re-home 后的入站引用完整性 —— `check_wikilinks.py` 的 A4 解析只覆盖 5 个根文件，
   `check_loop_section_refs.py` 的扫描面**排除** `plans/`，`find_stale_docs.py` 只匹配反引号路径且
   本单元不重命名任何路径。**没有任何 gate 会发现一个指向新工件的坏引用。**
3. **未**证明「PR-G 必然不早于 2026-09-11」—— 那是**按当前注册公式的条件性投影**。
   `policies/ci-gates.md` §3 W1/W2 允许 Owner 拍板豁免观察期，且仓内有把日历腿改判为 run-based
   early-accept 的执行先例。新工件 §1 已按条件性措辞书写。
4. **未**做任何 live / 外部依赖验证；未触达 `.env` / secrets / 任何数据库。

## 8. Stage 11 对抗性自评审记录

见 Stage 17 ledger（含完成 / 失败镜头数与**未经证伪的 finding 数**，如实披露）。

## 9. 与后续 unit 的接口

- **PR-D2**：入场读 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.2 + §5.1 + §5.3 + **§6.1
  翻转执行清单**（不再读 kernel plan §5.9 表）。⚠ §6.1 第 6 条要求把 `#499-F21` / `F20` /
  `#499-F22` 三件事分开写清；**F20 的恢复面是两处**（§3.1）。
- **将来的 V12 flip 单元**：读同一工件 §2.1 + §6.2。
- **PR-G**：把 kernel plan 翻 `completed` 时，§5.8/§5.9 只余指针存根 —— **不再有活体注册表被一并
  闭档**。⚠ 本工件 `state: active` 且**不随 PR-G 闭合**，其闭合条件见 §10（双路径）。
