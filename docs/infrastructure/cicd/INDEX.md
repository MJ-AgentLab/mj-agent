---
type: standard
domain: SYS
summary: docs/infrastructure/cicd/ 子目录索引 — mj-agent CI/CD 与发布流程的运维 runbook 入口；首份为 Release Process（Minimal 起步版）
owner: 项目负责人
created: 2026-05-06
updated: 2026-05-06
state: draft
track: code
---

# CI/CD 基础设施索引

> **所属目录**：`docs/infrastructure/cicd/`
> **说明**：覆盖 mj-agent 发布、双推、tag、CHANGELOG cut 等运维步骤的 RUNBOOK
> 入口。首份为 Phase 0.5 Minimal 起步版 `[RUNBOOK]_Release_Process.md`；
> Phase 1+ 增 deploy / CD / GitHub Actions 等章节或新文档。

---

## 文档列表

| 文档 | 类型 | 摘要 |
|------|------|------|
| [Release Process](./[RUNBOOK]_Release_Process.md) | RUNBOOK | mj-agent 发布运维流程 (Phase 0.5 Minimal 起步版)：CHANGELOG cut + version bump + git tag + 双推 + GitHub Release |

---

## 关联入口

- [返回上级索引](../../INDEX.md)
- [[../git/INDEX|infrastructure/git/]]（推送/分支/PR 操作 GUIDE）
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0|Commit Message v1.0]]（release 走 `infra(release):` 类型）
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]（git/commit 规范派生记录）

---

## 派生说明

mj-agent 原生（非派生）。
