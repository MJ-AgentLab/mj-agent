# #555 合并后同步与保留：Owner 审阅清单（2026-10-09）

## 已完成与需要选择的原因

正常只读复核确认 #566/#571/#574 均 MERGED，当前 OPEN PR 查询为空；正常 fetch 更新对象/跟踪 refs，未更新本地 develop。合并后原支持对话仍只有专员首答，AC-22/24 加载/恢复关联 UNKNOWN、#555 OPEN、Plan active。E13 与 Plan §29 已本地补记，尚未新增提交/发布。

19 份具名文件已在下列备份目录逐字节核对，未读取秘密或个人配置。mj-agent-git-sync 的 H1 要求 dirty 工作树先由 Owner 选择保存方式；根 AGENTS.md 第 4 项要求 Gitee develop 普通 push 独立获批。因此先交可审阅清单，再执行保存/同步；此前 15 文件交付和临时删除批准不覆盖本次范围。

- **A（推荐）**：批准 §2 的 16 路径临时保存、本地 fast-forward 到 `c449dff6`、从已核对备份逐字节恢复这 16 路径并保留 stash/备份；**另批准** §3 的 Gitee develop 守卫普通 ff。所有 worktree/发布分支保留，恢复后本地 5 份增量仍未提交。理由：保护未提交内容，并让本地及冗余镜像纳入已合并成果。
- **B**：仅批准 §2 本地保存/ff/恢复，Gitee push 留待后续决定。
- **C**：保留当前工作区和备份，暂不做保存/同步或镜像 push。
- **独立 D（推荐）**：发布 §5 的一条精确 #555 状态评论。此选项不随 A 自动批准。

本清单不含新 commit/PR、PR merge、关闭 Issue、state completed、本地删除、远端删除、配置/信任修改或新增附件/支持消息。

## 1. 精确对象、版本和备份

- 仓库：MJ-AgentLab/mj-agent，Gitee=`https://gitee.com/ranzuozhou/mj-agent.git`、origin=`https://github.com/MJ-AgentLab/mj-agent`。
- 当前工作树/分支：`D:/workspace/10-software-project/projects/mj-agent/develop` / develop。
- 当前 HEAD=`0b2f542e466fe36258046c7e8592ed6770e983f2`；目标 origin/develop=`c449dff6baec64b874f899431109fb3542e0ff4f`。本地 HEAD 是目标祖先；正常 fast-forward 不产生新 merge commit。
- 当前 Gitee refs/heads/develop=`4e55aae9d78f59ce9b47be43171b5fb33fe95049`，是目标祖先，0/25；仅考虑普通 fast-forward，目标或分歧变化则暂停核查。
- 原字节备份：`D:/workspace/10-software-project/projects/mj-agent/backups/issue-555/post-merge-20261009T094040Z`。19 份包含 16 个保存对象和三份既有交付 manifest/review/receipt；只复制，不移动、不删除原内容。
- [机器可读保存/备份清单](post-merge-sync-manifest-2026-10-09.json)，SHA256=`a15f21288b491ec44bc197c54d457971f29911ca0b96c186d8e1ba5421c099a0`，与备份目录 backup-manifest.json 原字节一致。
- 16 文件对应 incoming Git blob 均已读取：5 个保留本地增量，11 个 Git 内容相同。恢复所有 16 个原字节保证冻结正文/截图哈希，不回写任何其他已合并基线文件。
- 当前 cached diff 空，acceptance 有 intent-to-add flags=20004000。保存前只将该 acceptance 转为完整 index 内容，以便 stash 保留；此临时暂存不创建提交。此后保留 stash 与外部备份，恢复后新基线的所有 index 保持 clean，5 份本地内容仍为未暂存修改。

| 保存/恢复精确路径 | 字节 | SHA256 | incoming 对比 |
| --- | --- | --- | --- |
| `AGENTS.md` | 9215 | `fc68b6b9955aa0f4336f48c0b2bf467f1b3787e4d51a8100cbcc2a11a76b5f84` | 保留本地增量 |
| `evidence/issue-555/acceptance-2026-09-23.md` | 128712 | `a3e325ef2059d7f662962bee1a517bca67816e981b214faf286134130dbc37d8` | 保留本地增量 |
| `evidence/issue-555/ac24-desktop-diagnostic-request-2026-10-08.md` | 14559 | `0c81bd039e0a993ed2366174dad45e00678804213df7e0e60f90d888a73aedab` | 保留本地增量 |
| `evidence/issue-555/ac24-feedback-text-2026-10-08.md` | 1264 | `ba3a1e1743cce50fcc92a28a49a6f2ef1d9dd4b6d9276cc7adbb6bf9b051cfbe` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md` | 2243 | `b73d23e2ffb73009ba6c69a9e8e163acfe2a941209b5447f948c0eadbbe6c486` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-pr-body-2026-10-08.md` | 2235 | `ed1514f2dd708c0d931cb6dcfb9e411af0defb38d1b2c4e18eeaa1dde33871c6` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-remaining-scope-options-2026-10-08.md` | 9422 | `ab387f27aa33863b17a9ab036c254b8b61ee3617fccd0b22a6118ff7a9281f34` | 保留本地增量 |
| `evidence/issue-555/ac24-support-email-gate-2026-10-08.jpg` | 220036 | `c724c81353ba90d81d71de9eca25377d443f7219c31bb2eefea788a7c4e2ab3b` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-support-escalation-2026-10-08.jpg` | 186208 | `2d42edfff7a99313613a64fbd223631f46fe8ab1bbf3bf4b53de6d1e4bed6e61` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-support-reply-2026-10-09.jpg` | 185368 | `49613dfd6c9122f0086f2f1c48f49055578e3fd500a158991da0a81c7416cb01` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/ac24-support-request-2026-10-08.md` | 2922 | `0d3e5c561b884c4232b1985fd7a60fb86558885066c5a4cbdaba037a22ee5ee4` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/current-clauses-2026-10-09.json` | 11694 | `bc42f54fb5b9ab717a878321948ea1440b60df53bea25bd99b00c1aa4563ac8b` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/consistency-review-2026-10-09.md` | 8916 | `cedb56d5727a89d3d8f4e16838bf99278a8dff190bc319c982e7d73ae280b0dc` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/records-pr-body-2026-10-09.md` | 3493 | `b9fdfc44e6904dcf566518ec75baa66a431aa18960580bb95e4d984be7e8b0ad` | Git 内容与 incoming 相同，恢复原字节 |
| `evidence/issue-555/records-issue-comment-draft-2026-10-09.md` | 1687 | `5fe34a2b195673c595520dd74122b94b74fb47d24ce2492f15abe77248e18a0b` | Git 内容与 incoming 相同，恢复原字节 |
| `plans/[PLAN]_555_approved_deletion.md` | 87801 | `d4a23d7aefb8899f4b8e86f58da84a1447b9075c953f17caa1db176813c52afe` | 保留本地增量 |

`.playwright-mcp/`、其他任务工作树、三份既有交付控制/回执、当前 post-merge 本地审阅文件和评论草案均不进入保存/暂存清单，原地保留。禁止文件不打开、不哈希。对来源/备份/路径/HEAD/内容的实质变化只暂停受影响项。

## 2. 预期本地保存、fast-forward 与恢复（尚未执行）

在上述 develop 工作树执行前，逐一复核 source/backup SHA、16 路径/原 index 和 origin/develop 目标、当前其他未跟踪文件不会与 incoming 冲突。

```powershell
git status --porcelain=v1 --untracked-files=all
git diff --cached --numstat
git rev-parse HEAD
git rev-parse origin/develop
git add -- evidence/issue-555/acceptance-2026-09-23.md
git diff --cached --name-only
git stash push --include-untracked -m "issue-555-preserve-before-ff-20261009T094040Z" -- ':(literal)AGENTS.md' ':(literal)evidence/issue-555/acceptance-2026-09-23.md' ':(literal)evidence/issue-555/ac24-desktop-diagnostic-request-2026-10-08.md' ':(literal)evidence/issue-555/ac24-feedback-text-2026-10-08.md' ':(literal)evidence/issue-555/ac24-issue-comment-draft-2026-10-08.md' ':(literal)evidence/issue-555/ac24-pr-body-2026-10-08.md' ':(literal)evidence/issue-555/ac24-remaining-scope-options-2026-10-08.md' ':(literal)evidence/issue-555/ac24-support-email-gate-2026-10-08.jpg' ':(literal)evidence/issue-555/ac24-support-escalation-2026-10-08.jpg' ':(literal)evidence/issue-555/ac24-support-reply-2026-10-09.jpg' ':(literal)evidence/issue-555/ac24-support-request-2026-10-08.md' ':(literal)evidence/issue-555/current-clauses-2026-10-09.json' ':(literal)evidence/issue-555/consistency-review-2026-10-09.md' ':(literal)evidence/issue-555/records-pr-body-2026-10-09.md' ':(literal)evidence/issue-555/records-issue-comment-draft-2026-10-09.md' ':(literal)plans/[PLAN]_555_approved_deletion.md'
git rev-parse refs/stash
git stash list
git diff --cached --numstat
git status --porcelain=v1 --untracked-files=all
git merge --ff-only c449dff6baec64b874f899431109fb3542e0ff4f
git rev-parse HEAD
```

在 stash 后记录其实际 SHA，核对保存树/index/untracked 子树精确覆盖清单内容；确认已保存的 16 路径不阻碍 ff。结果未知先查 HEAD、refs/stash、index、source 和备份，不重复未知 stash。stash 不存在/内容不完整则停止同步，不假定备份与保存动作成功。

ff 成功后，使用正常文件工具从 manifest 中 16 个 backup_path 原字节复制回对应 source_path。只复制这 16 文件；操作前再次核对绝对路径均在 develop、不是重解析点，备份哈希未变，incoming 文件没有并发修改。因为 original 工作区记录含尚未合并的 E12/E13 增量，恢复采用已批准字节，不运行 stash pop，不 drop stash、不清理目录。此固定恢复方案是待 Owner 审阅的正常数据保护步骤，不是拒绝后的替代路线；若工具实际拒绝，不换工具或改写重试。

恢复后验证 16 文件 raw SHA 和当前预期 blob、HEAD=目标、tracked diff 精确为 AGENTS/验收/诊断/选项/Plan 5 路径、index 内容 clean、.playwright-mcp/ 哈希和原地状态未变，其他记录/回执均保留。AGENTS 原两行原则仅被保留，不新增治理或 trust 决定。保留原 stash 与外部备份，其他任务未提交内容不动。

## 3. 独立普通 push 授权：Gitee develop 镜像 ff（尚未执行）

准备时预期 origin=`c449dff6baec64b874f899431109fb3542e0ff4f`、Gitee=`4e55aae9d78f59ce9b47be43171b5fb33fe95049`。执行前重新只读核对两个实际 tip、来源变化与祖先关系；不能把旧跟踪 ref 当成实时事实。按项目 Stage17 使用守卫脚本，不修改脚本/配置：

```powershell
git ls-remote --heads origin refs/heads/develop
git ls-remote --heads gitee refs/heads/develop
pwsh scripts/sync-gitee-mirror.ps1 -Branch develop -Remote gitee -Source origin
git ls-remote --heads gitee refs/heads/develop
git ls-remote --heads origin refs/heads/develop
```

脚本自行 fetch 两端，只允许 ff，分叉拒绝 exit 3；实际来源变化先重新核对 scope，不能因聊天批准推定新 tip 已获核查。此 push 仅 Gitee refs/heads/develop；不普通推送 origin/develop、不 force，不推或删三条发布分支。成功后用独立 ls-remote 验证两端实际 SHA；响应未知先对账，成功动作不重复。

## 4. #555 三条发布分支/工作树：保留，删除尚未准备为 READY

| 分支 / 本地工作树相对项目根 | 本地及 Gitee tip | origin/final PR head | merge / 本地状态 |
| --- | --- | --- | --- |
| codex/555-ac9-publish-20260923 | 878b474d56e1e4201bba335b60caa9ad7ee018cd | 4f867694f3537fcb77c6b81d379b1b4d4454ff2e | #566 merge 4334a577；无 tracked/untracked/ignored |
| codex/555-ac24-load-publish-20260923 | 6d331438990c458599025bccf3196fabbd694514 | 7cbf5ebed4d436c92cd3ac7404cb75264e12b1ce | #571 merge 2f707200；无 tracked/untracked/ignored |
| documentation/555-acceptance-records-20261009 | 837c4b49b20c2484a878aad398c643e4ffc71852 | 967fc845b9a895157ce6ebd131cd99f6f169a929 | #574 merge c449dff6；十份 ignored pyc |

三组 local/Gitee/origin/merge 均已包含于目标 develop，但两端 tip 不同，删除批次保留暂停；第三 worktree 的 ignored 内容未获删除批准。三者 tracked flags H、未发现重解析点；尚无删除时刻文件占用核查，不能称已全部 READY。将来清理先准备逐端精确 ref/tip、合并证据、ignored 备份及占用清单，再分别决定本地和远端删除。旧 S/A/B 清理批准不覆盖这些发布分支。当前 A/B/C 选择均保留它们。

## 5. 独立 D：状态评论（尚未发布）

[评论精确草案](post-merge-status-comment-draft-2026-10-09.md)，SHA256=`be95aba28209638039a4df06a42a197b2cdc93b7c6c90bcad2c58c7d52b9b28b`。仅 MJ-AgentLab/mj-agent #555 的一条状态评论，无附件；标题注明准备快照，合并与加载 UNKNOWN 分列。

```powershell
gh issue comment 555 --repo MJ-AgentLab/mj-agent --body-file evidence/issue-555/post-merge-status-comment-draft-2026-10-09.md
gh issue view 555 --repo MJ-AgentLab/mj-agent --json state,updatedAt,comments,url
```

执行前查精确内容是否已发布；未知响应先对账，不重复。回读实际 URL、createdAt、正文 SHA，确认 OPEN。原完整正文 64 KB 拒绝仍 BLOCKED_EXECUTION_ROUTE，不重试、不换编码/分块绕过。

## 6. 原错与最小剩余验收

实际宿主拒绝保留完整原错/命令/UTC/call，暂停受影响路线，不换工具、改命令、建凭证或改权限绕过。Git 普通错误和宿主拒绝分别定位；定位不了则 UNKNOWN。ff 失败不会自动 reset/rebase/force；源文件、stash 和备份先逐项对账，再交具体条件/选择。没有 merge commit 或新 Git 发布授权。

已完成：三 PR MERGED 与对象/祖先核对、只读支持核查、19 文件备份、E13/Plan§29 本地记录。文档检查 frontmatter 147 PASS（2f9c1e）、wikilinks 0/0（7444a0）、链接/尾空白/diff/Playwright/旧工作树内容保留 PASS（2be937），均 exit 0；备份原字节/19 个哈希与 5 个增量分类 PASS（cc0c0e）。这些检查不证明实际加载。当前任务工具权限声明 never，与 Desktop 历史事件分列。

剩余实质验收：目标实例可追溯来源/定义哈希、项目和 hook 信任、实际加载或跳过/原因/时间、有效模式及恢复关联，或 Owner 明确调整剩余范围。原时段 UNKNOWN 永久保留；#555 OPEN、Plan active，不建议关闭。BDD/TDD=NONE，未委派，不启动 infra/live probe，不新建其他 Issue/任务。

最终准备核对：`84f6ce` exit 0，19 份 source/backup 字节和 SHA 全匹配、16 保存路径精确、双份 manifest 同字节/哈希一致，review 链接/尾空白/JSON PASS；本地 HEAD 未变、origin 目标 c449dff6、Gitee gap=25，cached diff 空、Playwright 哈希未变、diff --check exit 0。`161310` exit 0，再次查询当前 OPEN PR 为 []，#555 OPEN、updatedAt=2026-10-09T08:49:41Z。没有执行 stash/ff/push/删除或发布新评论。
