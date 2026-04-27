---
name: Maintain PR
about: CI/CD、依赖、脚本等基础设施维护 (maintain/*) 的 Pull Request
---

## 变更摘要
<!-- 简述本次维护变更的内容和目的 -->

## 影响评估
<!-- 列出受影响的环境（开发/CI）、工具链或依赖 -->

## 审核要点
<!-- 提示审核者重点关注的内容 -->

## 自检结果
- [ ] 配置文件语法正确（YAML / TOML / JSON）
- [ ] GitHub Actions 工作流不受影响（或已同步更新）
- [ ] 无硬编码敏感信息（密钥、令牌、IP、密码）
- [ ] Commit message 符合规范（仅含 `infra` / `docs` 类型）

## 文档自检
- [ ] 若变更影响运行入口、关键环境变量、依赖版本，`CLAUDE.md` 已同步检查（A6）
- [ ] 若新增/修改 PR 模板或 CI 工作流涉及 A1-A10 校验，`[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md` 已同步
