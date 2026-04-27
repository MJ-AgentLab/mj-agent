---
type: contract
domain: TOOL
summary: 20-60 字摘要，一句话说清楚此 contract 约束哪对接口
owner: 项目负责人
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v1.0
contract_kind: tool
parties: []
schema_ref: ""
---

# Contract: <Name>

> 复制本模板到 `docs/contracts/[CONTRACT]_<Kind>_<Name>_vX.Y.md`。
>
> `contract_kind`：`tool`（进程内工具接口） / `cross-service`（跨仓库/跨服务） / `mcp`（MCP server）。
> `state: active` 时 `schema_ref` 必填且指向存在的机器可读 schema 文件（A10）。

## Parties

- **Provider**：谁提供这个接口（实现方）
- **Consumer**：谁消费这个接口（调用方）
- `parties` frontmatter 字段应列出项目/服务名称

## Interface schema

引用机器可读 schema（JSON Schema、OpenAPI、Protobuf、Python 类型签名）。
schema 源文件相对路径放在 `schema_ref` 字段。

```yaml
# 示例：工具签名
name: example_tool
input:
  foo: string
  bar: int (optional)
output:
  result: list[dict]
  truncated: bool
```

## Inputs / Outputs

用人类语言解释每个字段的语义与取值范围。
机器 schema 负责结构校验，本节负责意图说明。

## Error modes

| 错误类型 | 触发条件 | Consumer 应如何处理 |
|----------|----------|---------------------|
| `...` | ... | ... |

## SLO（可选）

- 延迟 p95：<值>
- 可用性：<值>
- 速率限制：<值>

## Versioning policy

- 增量字段（加字段）走 minor 版本升级
- 删除/改语义字段走 major 版本升级
- Major 升级时保留旧版至少一个发布周期（`state: deprecated`）
