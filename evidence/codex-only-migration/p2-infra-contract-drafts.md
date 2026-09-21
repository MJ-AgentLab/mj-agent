# P2：8 项 infra 契约修订草案

DRAFT_NOT_APPLIED。没有写正式契约、frozen_at 或正式冻结摘要。完整旧/新description、body逐行diff、节标题与恢复身份见 JSON。

摘要算法沿用契约：description 取文本scalar；body剥离首个frontmatter并LF规范化，不trim；UTF-8 SHA-256。

## mj-agent-infra-app-start
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-app-start/SKILL.md` → 新 `.agents/skills/mj-agent-infra-app-start/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-app-start/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:ac3dcb53efc27c435888c886272594b798ca87f49a6d8573ed7b025f8c7e0c07 | sha256:5a80607da91bac49f466fabc210e5fb8f16921d5ca537945b9873a7ea40809d2 |
| body | sha256:9ab21e612642ee925a9e3340777f3d2c77aadc9f498a904a38ea5828b0786170 | sha256:344f85c860f0a6be29b418263a2fa200bc4f078b571c7a0dbaf7d073f3884c59 |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-start/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-app-stop
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-app-stop/SKILL.md` → 新 `.agents/skills/mj-agent-infra-app-stop/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-app-stop/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:2181768f5aefd448aa1b0bd6f65865ab86b887897b85016f7d766ecdae613301 | sha256:e877e20924484e642937a21c622a6ffdb65a5b81d949e179a0ab16ef7893f9b0 |
| body | sha256:2ed0c015e41e97aac5e7564b752b2a5d38e371a8c4f7f193b485224c3cff591a | sha256:2a785bc1efe9b498634f45c600eed60df9485b780e94b221632588f42c367c0e |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-app-stop/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-docker-compose
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-docker-compose/SKILL.md` → 新 `.agents/skills/mj-agent-infra-docker-compose/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-docker-compose/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:013d8ec2c3db8d3a814d7db516cc92cedb5dab4f12e34fbe6070a68e162ce002 | sha256:edc35321cc8397e459f3c2c66f884f6ff1321fa5a3b25a366e0109a211db8dc3 |
| body | sha256:3c68d460960e8f406068f19df16d9a7bb807f9f892019ea2d801f5fce716929f | sha256:3480751bdacf2eceff202fa0479b74e69634f23f4cbb193e433ae7a7b9726018 |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-docker-compose/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-env-setup
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-env-setup/SKILL.md` → 新 `.agents/skills/mj-agent-infra-env-setup/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-env-setup/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:d0c1bfa84b8143f3ff5d5d6a33b92b79857ad8135265b999f349075b25643745 | sha256:38d8b4a0cf75f1eae01f44dff9ddc2306472635533f95c4a9d5394e53e2c0c06 |
| body | sha256:402d9b748cdee70bc8eb2134bcedb4cecc380fc20390df36d3c6dc97116e8e0f | sha256:248f84f521fa564544bd8cf963fcdf04f78dd6166ecfe6f48a70b0259e7f5e4f |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-setup/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-env-teardown
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-env-teardown/SKILL.md` → 新 `.agents/skills/mj-agent-infra-env-teardown/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-env-teardown/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:388b327abd3b9d833be0977e4d39cd5e5a25d4ef534edfded030da2d207516a1 | sha256:4c96cbdf48388759c44edf7f7c1530333d1672a126fe7b031f42b593ed0d67ea |
| body | sha256:8963f817783010555754c6136bc931c66f6023638b4c2dbdf1209854e079318a | sha256:d6f1c48d67802fadcf3392eaf158000785d0926cd975c329c8d0dc3dd6f17bb8 |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-env-teardown/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-llm-endpoint-probe
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` → 新 `.agents/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:4ab5f6edbf47495a3b40f183ba2736cd96b9665c9ee9b68608392a2e44d16bff | sha256:bd4a60e9b2b0a53fc23646645b79d74ba3a9993726c32ac70644b7c178e993ed |
| body | sha256:5e53851599a3e3dc623028e3d02be2c1a72272562c24e28a2ad2be5898d09531 | sha256:a8101c179ffa9e51c14a34445e7d3f1d2998de74f8fea37f90266978beea61a4 |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-storage-stack
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-storage-stack/SKILL.md` → 新 `.agents/skills/mj-agent-infra-storage-stack/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-storage-stack/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:d1a7c9bc66b5a1369f94d0d43ce3ab8acd1c86aa3a5e269bd9034035abff97d1 | sha256:bf2b3ec55ed335baa2b26f098bc272f45aa3907b12c7efe81ab2004ccda56562 |
| body | sha256:b4e4ec4dce74f04c011d3e1accd5d838e59ca7d6f9fba7da9d05431b45b63572 | sha256:5f0939fd0f32863aea912614cd0d78aa84bfdc316ea4bb997a0a2f8a95b312b6 |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-storage-stack/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

## mj-agent-infra-studio-probe
契约 `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；旧 `.claude/skills/mj-agent-infra-studio-probe/SKILL.md` → 新 `.agents/skills/mj-agent-infra-studio-probe/SKILL.md`。
候选 `.migration/codex-only/project/.agents/skills/mj-agent-infra-studio-probe/SKILL.md`；旧冻结复算匹配：True。
| 对象 | 旧摘要 | 新摘要 |
|---|---|---|
| description | sha256:3b01bf7bc5b2c9f7671bbb97cfe6ba0ddf8cb7d9a96a9d27fcd896bfc77e9edd | sha256:810dcc24cf5037855e61309971df9a8826a96d2457b21ebe9302455d50559104 |
| body | sha256:fcb36d85ff40bd7fbff3056688851ebb7dab87dab97932b5ba49296b2e3d4bf6 | sha256:c801f70334899d34d50230ee7c2c00c709e2061bcb0f9b14b7b1f26cd9f582ff |
description 改写：原触发/排除语义保留；客户端、项目MCP范围、实际工具及批准执行关系按候选说明更新。
body 改写：完整原步骤作基线；原生路径/共用边界，去宿主虚构和旧凭据范围；危险恢复只在具名批准及执行路线可用时处理；缺能力标UNMET。
恢复 `20e2f24c352cf640d9dd33234b128ca897804b99:.claude/skills/mj-agent-infra-studio-probe/SKILL.md` + `20e2f24c352cf640d9dd33234b128ca897804b99:capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`；必须成组恢复，不覆盖新身份。
P3前置：逐项Owner批准、候选重新核hash、确定冻结时间与本契约直接消费者字段；本阶段不应用。

