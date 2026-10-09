# #555 记录交付：Owner 具名审阅与授权清单（2026-10-09）

## 准备结果与推荐选择

本次准备已完成：15 份 payload 已原字节复制到独立 documentation 工作树，暂存区为空，没有新提交、推送、PR 或评论发布。工作树由正常 git worktree add 创建，原 develop 和有内容旧工作树保留。此清单及 manifest 仅留在原 develop 供本地审阅，不纳入提交。

根 AGENTS.md 第 4 项与 ADR-034 要求 commit、普通 push、PR 创建分别获得 Owner 具名批准；Issue 评论也是独立外部发布。历史 canary 授权和本轮准备授权不覆盖这些记录。

- **A（推荐）**：批准 C1/C2 的 15 份具名文件提交、产生的精确新分支 tip 普通双推、显式 base=develop 的 Draft PR。三类批准独立。理由：已完成的验收与诊断进展可进入可审阅 PR，AC-22/24 的未知仍保留。包括公开下列元数据/支持截图的决定，需先审阅。
- **B**：仅批准 C1/C2 提交，保持本地。后续普通 push、PR 另行决定；本地记录有固定 commit SHA，但尚不公开。
- **C**：仅保留准备结果。若希望缩减公开字段/截图，指出精确范围，Codex 先准备新 payload/哈希再交审阅，冻结原始证据不改写。
- **独立选项 D**：是否批准发布本清单 §5 的一条具名 #555 状态评论。它不随 A 自动批准，不改变正文或关闭状态。

## 1. 对象、tip、备份与公开范围

- 仓库：MJ-AgentLab/mj-agent，PUBLIC。
- 工作树：`D:/workspace/10-software-project/projects/mj-agent/documentation/555-acceptance-records-20261009`。
- 分支/双端精确引用：`documentation/555-acceptance-records-20261009` / `refs/heads/documentation/555-acceptance-records-20261009`。
- 当前 HEAD / origin develop 基线：`0b2f542e466fe36258046c7e8592ed6770e983f2`。新记录没有 commit SHA；后续只允许 C1/C2 两个批准的 payload 提交形成的新 tip，执行前后均读取/登记实际 SHA，推送前重新核对两个 commit 与下表文件/blob。
- Gitee develop：`4e55aae9d78f59ce9b47be43171b5fb33fe95049`，是基线祖先，left/right=0/2。只推新分支，不推或同步 develop。
- 两端新 ref 的准备时快照均不存在，同 head 已有 PR 查询为空；查询失败不等于不存在，实际发布前重新查询。
- Gitee：`https://gitee.com/ranzuozhou/mj-agent.git`；origin：`https://github.com/MJ-AgentLab/mj-agent`。
- 内容保留依据：全部 payload 同时保留在原 develop 和新工作树且逐文件原字节一致；无删除动作，不要求合并证明。将来的本地 commit 不覆盖原副本，不包含 reset、stash、force-push、merge、清理或信任/配置修改。
- 公开审阅：验收/Plan 有既有 Git 作者邮箱，记录有本机路径、线程/turn/进程标识；三份支持截图有账户显示名与对话内容（邮箱输入截图只见空输入和占位符）。这是 PUBLIC 仓库的新公开内容范围，须随 15 文件决定。未读取/摘要 `.env`、secrets、个人凭据或配置；有限扫描无凭据格式命中不能保证没有其他敏感内容。

[机器可读文件清单](records-delivery-manifest-2026-10-09.json)，SHA256=`36b1531f0a30e2e5141f4fd143e0c2978d7e5b4224fe6d9d9a581fcc215ced40`。哈希输入为实际工作树文件原字节；manifest 同时列 expected_git_blob，覆盖 Git 正常换行转换。Git 作者沿用实际配置并在执行后登记，不伪造署名。

| 提交 | 精确文件 | 字节数 | SHA256 |
| --- | --- | --- | --- |
| C1 | `evidence/issue-555/acceptance-2026-09-23.md` | 114923 | `53091a1e488b7a47fb1b314397787230b87123e55ee0fd178805842b88ecb5bf` |
| C1 | `evidence/issue-555/ac24-desktop-diagnostic-request-2026-10-08.md` | 13590 | `8a6f328811aa9a9dfc2f7d916d83e8503a9b8e9f13bd024d65f4ec39b769a1c2` |
| C1 | `evidence/issue-555/ac24-feedback-text-2026-10-08.md` | 1264 | `ba3a1e1743cce50fcc92a28a49a6f2ef1d9dd4b6d9276cc7adbb6bf9b051cfbe` |
| C1 | `evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md` | 2243 | `b73d23e2ffb73009ba6c69a9e8e163acfe2a941209b5447f948c0eadbbe6c486` |
| C1 | `evidence/issue-555/ac24-pr-body-2026-10-08.md` | 2235 | `ed1514f2dd708c0d931cb6dcfb9e411af0defb38d1b2c4e18eeaa1dde33871c6` |
| C1 | `evidence/issue-555/ac24-remaining-scope-options-2026-10-08.md` | 8413 | `0e902675e3c6a536e220f9c6f6cf92497fbe5663abc9689f62d7bb5e70d05c5e` |
| C1 | `evidence/issue-555/ac24-support-email-gate-2026-10-08.jpg` | 220036 | `c724c81353ba90d81d71de9eca25377d443f7219c31bb2eefea788a7c4e2ab3b` |
| C1 | `evidence/issue-555/ac24-support-escalation-2026-10-08.jpg` | 186208 | `2d42edfff7a99313613a64fbd223631f46fe8ab1bbf3bf4b53de6d1e4bed6e61` |
| C1 | `evidence/issue-555/ac24-support-reply-2026-10-09.jpg` | 185368 | `49613dfd6c9122f0086f2f1c48f49055578e3fd500a158991da0a81c7416cb01` |
| C1 | `evidence/issue-555/ac24-support-request-2026-10-08.md` | 2922 | `0d3e5c561b884c4232b1985fd7a60fb86558885066c5a4cbdaba037a22ee5ee4` |
| C1 | `evidence/issue-555/current-clauses-2026-10-09.json` | 11694 | `bc42f54fb5b9ab717a878321948ea1440b60df53bea25bd99b00c1aa4563ac8b` |
| C1 | `evidence/issue-555/consistency-review-2026-10-09.md` | 8916 | `cedb56d5727a89d3d8f4e16838bf99278a8dff190bc319c982e7d73ae280b0dc` |
| C1 | `evidence/issue-555/records-pr-body-2026-10-09.md` | 3493 | `b9fdfc44e6904dcf566518ec75baa66a431aa18960580bb95e4d984be7e8b0ad` |
| C1 | `evidence/issue-555/records-issue-comment-draft-2026-10-09.md` | 1687 | `5fe34a2b195673c595520dd74122b94b74fb47d24ce2492f15abe77248e18a0b` |
| C2 | `plans/[PLAN]_555_approved_deletion.md` | 82999 | `0fb49be5941e9f5a32c24fc5f584467920c50a605a83180acb461f13f04e121b` |

排除：AGENTS.md 的另行治理原则、.playwright-mcp/、历史 proposed diff、此清单与 manifest、其他 Issue、源码/测试/配置。三条有内容旧工作树仍分别有 2/0、5/1、7/475 tracked/untracked，全部保留。

## 2. 执行前复核与授权 C1/C2：提交

以下为预期正常工具命令，**尚未执行**。在上列新工作树运行；源内容/hash/目标范围实质改变时仅暂停受影响动作重新交审阅。

```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=all
git diff --cached --numstat
git diff --check
git add -- 'evidence/issue-555/acceptance-2026-09-23.md' 'evidence/issue-555/ac24-desktop-diagnostic-request-2026-10-08.md' 'evidence/issue-555/ac24-feedback-text-2026-10-08.md' 'evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md' 'evidence/issue-555/ac24-pr-body-2026-10-08.md' 'evidence/issue-555/ac24-remaining-scope-options-2026-10-08.md' 'evidence/issue-555/ac24-support-email-gate-2026-10-08.jpg' 'evidence/issue-555/ac24-support-escalation-2026-10-08.jpg' 'evidence/issue-555/ac24-support-reply-2026-10-09.jpg' 'evidence/issue-555/ac24-support-request-2026-10-08.md' 'evidence/issue-555/current-clauses-2026-10-09.json' 'evidence/issue-555/consistency-review-2026-10-09.md' 'evidence/issue-555/records-pr-body-2026-10-09.md' 'evidence/issue-555/records-issue-comment-draft-2026-10-09.md'
git diff --cached --name-only
git diff --cached --check
git commit -m "docs(evidence): preserve #555 acceptance and diagnostic records"
git show --format=fuller --stat HEAD
git add -- ':(literal)plans/[PLAN]_555_approved_deletion.md'
git diff --cached --name-only
git diff --cached --check
git commit -m "docs(plans): retain #555 host loading acceptance as active"
git show --format=fuller --stat HEAD
git rev-parse HEAD
git diff --name-status 0b2f542e466fe36258046c7e8592ed6770e983f2..HEAD
git status --porcelain=v1 --untracked-files=all
```

每次提交前逐文件 SHA256/expected_git_blob 对照 manifest，index 精确等于对应组；C1 不提交 Plan，C2 仅 Plan。C1/C2 生成后用 git log/tree 对账只有两次 docs 提交、15 个路径及期望 blob；工作树须清洁。提交未完成或结果未知时先读取 HEAD/提交内容/index，对账后继续，不重复未知 commit。当前 never 不能单独推定 Git 被拒绝或获宿主许可；实际拒绝按原错停点处理。

## 3. 独立授权：Gitee→origin 普通双推

提交对账成功后重新核对 remote URL、两个精确 ref 和同 head PR。将实际 HEAD 记为发布 tip（此时不是基线）；只允许该 tip 的具名新分支普通发布。

```powershell
git remote get-url gitee
git remote get-url origin
git ls-remote --heads gitee refs/heads/documentation/555-acceptance-records-20261009
git ls-remote --heads origin refs/heads/documentation/555-acceptance-records-20261009
git push gitee documentation/555-acceptance-records-20261009:refs/heads/documentation/555-acceptance-records-20261009
git ls-remote --heads gitee refs/heads/documentation/555-acceptance-records-20261009
git push origin documentation/555-acceptance-records-20261009:refs/heads/documentation/555-acceptance-records-20261009
git ls-remote --heads origin refs/heads/documentation/555-acceptance-records-20261009
```

每端成功均记录原工具回执、exit、UTC 与 ls-remote tip=实际发布 SHA；一端成功不能证明另一端成功。预检发现原不存在 ref 已出现不同 tip，暂停该端。响应未知先查询该端引用，查询失败保留 UNKNOWN；已成功端不重复推送，不 force，不删除其他引用。

## 4. 独立授权：Draft PR

[PR 正文](records-pr-body-2026-10-09.md) SHA256=`b9fdfc44e6904dcf566518ec75baa66a431aa18960580bb95e4d984be7e8b0ad`；标题 `docs: record #555 acceptance and pending host diagnostics`，head=documentation/555-acceptance-records-20261009，base=develop，Draft。相关 #555，不使用自动关闭词。

```powershell
gh pr list --repo MJ-AgentLab/mj-agent --head documentation/555-acceptance-records-20261009 --state all --json number,state,isDraft,headRefName,baseRefName,url
gh pr create --repo MJ-AgentLab/mj-agent --head documentation/555-acceptance-records-20261009 --base develop --title "docs: record #555 acceptance and pending host diagnostics" --body-file evidence/issue-555/records-pr-body-2026-10-09.md --draft
```

响应后按实际 URL/编号读取 head/base/head SHA/state/isDraft/body 并逐项核对，再用客户端 attach_artifact 关联已创建 PR；不能编造 URL。响应丢失先按 head 查询并比对，不重复创建。不要自动 merge/关闭 #555；AC-22/24 UNKNOWN、Plan active。

## 5. 独立可选授权 D：一条状态评论

[评论草案](records-issue-comment-draft-2026-10-09.md) SHA256=`5fe34a2b195673c595520dd74122b94b74fb47d24ce2492f15abe77248e18a0b`，只在 MJ-AgentLab/mj-agent #555 发布这一条精确正文。无附件、正文改写、close、Git 或删除授权。

```powershell
gh issue comment 555 --repo MJ-AgentLab/mj-agent --body-file evidence/issue-555/records-issue-comment-draft-2026-10-09.md
gh issue view 555 --repo MJ-AgentLab/mj-agent --json state,updatedAt,comments,url
```

先检查现有评论是否已含该精确内容；发布后保存实际 URL/createdAt/回读正文 SHA256 并确认 OPEN。结果未知先只读查 comments，不能因响应丢失重复发。完整正文准备的 64 KB 原始拒绝仍 BLOCKED_EXECUTION_ROUTE；此独立评论不解除该路线。

## 6. 原始错误、对账及验证证据

- 真正宿主拒绝：保留工具原错、call/chunk、UTC、实际命令和当时对象；停止受影响步骤，定位不了则 UNKNOWN/BLOCKED_EXECUTION_ROUTE。不得换工具、编码分块、改写拒绝命令、建凭证或改权限绕过。聊天新批准/网络恢复不能独自解除旧拒绝。
- 源文件校验：frontmatter 147 PASS（e258c5），wikilinks archive-ref 0/root unresolved 0（088d13）；15 文件/24 条/冻结哈希/扫描/diff/index PASS（f400fd），均 exit 0，详见验收 E11。
- 原字节复制 15 份、index 空（315541），exit 0；新工作树 frontmatter 147 PASS（fc40b4）、wikilinks 0/0（3f85ec），均 exit 0。
- 补充校验第一次 b81432 exit 1：原始 AssertionError 在 AGENTS 原字节与 HEAD blob 比较。只读复核 e6a545 确认 checkout 112 CRLF、blob 0 CRLF，正常换行归一后相同且 git diff --quiet AGENTS exit 0；这是比较器条件问题，没有宿主拒绝或 AGENTS 修改。修正比较后 15 份源/目标字节一致、链接/尾空白/JSON/diff/空 index PASS，exit 0，2026-10-09T08:37:23.383470+00:00。
- 纯记录范围，BDD/TDD=NONE、委派=NONE；复用历史 T1/T2，不重复功能测试。文档/格式检查不证明 rules/hooks 实际加载。
- 当前 22 项在各条款范围内已验证；AC-22/24 actual-loading/recovery UNKNOWN。支持首答后仍等待来源/定义哈希、信任、加载或跳过/原因/时间与恢复关联，或 Owner 明确调整范围。原时段 UNKNOWN 永久保留；#555 OPEN、计划 active。

最终冻结复核（chunk `bf8323`，exit 0）：manifest 15 路径/字节/SHA256/预期 Git blob 全匹配、审阅清单链接和尾空白 PASS；目标 status 精确为 payload、原/新工作树 index 均空、HEAD 仍基线，无自动关闭词，两个 diff --check 均 exit 0。只读 Issue 与 remote 复核（chunk `7c7423`，exit 0）仍 OPEN、updatedAt=2026-10-08T05:27:34Z，两个 URL 与清单一致。此后 payload/manifest 未改动，没有实际交付动作。
