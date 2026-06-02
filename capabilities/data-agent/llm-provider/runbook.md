---
type: capability-runbook
capability: data-agent.llm-provider
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: LLM Provider Abstraction

> Phase M1 baseline.

## §1 Startup

Provider selection via env. Default: `LLM_PROVIDER=ark` if unset.

### Ark (cloud; default)

```dotenv
LLM_PROVIDER=ark
ARK_API_KEY=<team key>     # OR set LLM_API_KEY (new generic; preferred)
# ARK_BASE_URL defaults to https://ark.cn-beijing.volces.com/api/v3
# LLM_THINKING_ENABLED=false (default)
# LLM_MODEL_ID=deepseek-v3-2-251201 (default)
```

### Local-openai-compat (DGX-Spark vLLM/SGLang/Ollama)

```dotenv
LLM_PROVIDER=local-openai-compat
LLM_BASE_URL=http://192.168.0.189:8000/v1     # required
LLM_API_KEY=<endpoint key OR leave empty for "EMPTY" sentinel>
LLM_MODEL_ID=<as configured on endpoint>
```

Verify before graph build:

```bash
uv run mj-agent check
# Expected on success: "llm provider = ark (endpoint=https://ark.cn-beijing.volces.com/api/v3)"
# Or: "llm provider = local-openai-compat (endpoint=http://192.168.0.189:8000/v1)"
```

Probe endpoint reachability (out-of-scope of this capability; delegated):

```bash
# Use the dedicated skill:
/mj-agent-infra-llm-endpoint-probe
# 3-step probe: reachable / model id match / 1-token chat smoke
```

## §2 Health Check

```bash
# Provider-aware credential validation (no endpoint contact)
uv run mj-agent check

# Unit tests (TBD-M3; current count: 0 for this capability)
uv run pytest tests/unit/test_llm.py tests/unit/test_config_llm_fields.py -q
# Phase M3 will land these test files; currently they don't exist.
```

## §3 Troubleshooting

### Symptom: `LLMConfigError: ARK_API_KEY not set ...`

**Diagnostic**：Ark provider selected (default) but no API key resolved through fallback chain.

**Resolution**：

- Set `ARK_API_KEY=<team-key>` in `.env` (or run `setup-env.ps1` to decrypt team bundle)
- OR set `LLM_API_KEY=<key>` (new generic; preferred since ADR-030 secrets bundle split)
- Both unset → error message instructs which env to set + suggests `setup-env.ps1`

### Symptom: `LLMConfigError: LLM_BASE_URL not set ...`

**Diagnostic**：local-openai-compat provider selected but `LLM_BASE_URL` empty. Ark fallback does NOT apply here.

**Resolution**：

- Set `LLM_BASE_URL` to your DGX-Spark endpoint:
  - vLLM: `http://192.168.0.189:8000/v1`
  - Ollama: `http://192.168.0.189:11434/v1`
  - SGLang: `http://192.168.0.189:30000/v1` (or wherever configured)
- Or switch back to `LLM_PROVIDER=ark`

### Symptom: 422 from local LLM endpoint with message about "extra_body" or "thinking"

**Diagnostic**：`extra_body.thinking` is being sent to a non-Ark endpoint. Should NOT happen if `LLM_PROVIDER=local-openai-compat` (REQ-002 design omits extra_body kwarg entirely).

**Resolution**：

- Verify `make_llm()` is using the correct branch: `uv run python -c "from src.mj_agent.config import settings; print(settings.llm_provider)"`
- If `LLM_PROVIDER` is `ark` but you're pointing at a local endpoint via env override → switch `LLM_PROVIDER=local-openai-compat`
- If contract regression (provider=local but extra_body still sent) → file `[BUG]` against this capability; REQ-002 contract violation

### Symptom: Settings construction fails with `pydantic.ValidationError` mentioning llm_provider

**Diagnostic**：`LLM_PROVIDER` env value is not in `{ark, local-openai-compat}`.

**Resolution**：

- Check env: `echo $LLM_PROVIDER`
- Fix typo (e.g. `LLM_PROVIDER=local` → `local-openai-compat`)
- This validation is eager (at Settings construction); fails fast

### Symptom: Endpoint reachable but model loading fails

**Diagnostic**：endpoint up but `LLM_MODEL_ID` doesn't match the loaded model.

**Resolution**：

- Use `/mj-agent-infra-llm-endpoint-probe` skill (step 2: model id match)
- Set `LLM_MODEL_ID` to match endpoint's served model name (e.g. for vLLM: `--served-model-name`)
- Default `deepseek-v3-2-251201` is Ark-specific; local endpoints typically have different IDs

### Symptom: `mj-agent check` reports LLM OK but `make_llm()` fails

**Diagnostic**：`mj-agent check` only validates env presence; `make_llm()` may fail on actual ChatOpenAI construction (e.g. network unreachable, malformed URL).

**Resolution**：

- `mj-agent check` is BY DESIGN credential-only — endpoint reachability delegated
- Use `/mj-agent-infra-llm-endpoint-probe` for actual endpoint test
- Common cause: VPN required for DGX-Spark WAN access; check network reachability separately

## §4 Related Artifacts

- `contracts/provider.contract.yml` — ark + local-openai-compat branch behavior
- `contracts/python.contract.yml` — llm.py + config.py + cli.py module APIs
- `contracts/behavior.feature` — 3 Gherkin scenarios
- `/mj-agent-infra-llm-endpoint-probe` skill — endpoint reachability + model id + 1-token smoke
- ADR-027 — LLM Provider Abstraction decision record
- `docs/runbook/dev_studio_walkthrough.md` — broader Studio context (Phase M5 dissolves)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 ark provider regression (existing prod users hit LLMConfigError unexpectedly)
- REQ-002 local provider sends `extra_body.thinking` to non-Ark endpoint (422 errors at scale)
- REQ-003 provider switch fails silently (operator changes LLM_PROVIDER but agent still uses old)

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md`.

---

## §7 Unautomated Scenario Justifications (M-FU#7)

> Per `sdd/adapters/bdd-tdd.md` L121 + L160 + L161 (G21+G22 share runbook
> justification source per R-15-1 resolution); BDD scenarios that are not yet
> automated must include 4-field justification (原因 / 替代验证手段 / 升级触发
> 条件 / 预计时间).

### G22/G21 Justification: Ark provider raises clear LLMConfigError when both ARK_API_KEY and LLM_API_KEY are empty

- **REQ**: REQ-001 / **Risk**: high / **Adapter**: python / **ADR-027**
- **原因**: M1 baseline + ADR-027 配置错误处理路径已落；BDD 层 step defs 推迟
  M3（与 safe-sql 同节奏）。
- **替代验证手段**: `src/mj_agent/llm.py` 实现已落 `LLMConfigError` 类 + Ark
  provider 分支（`make_llm()` 检 `effective_llm_api_key` 缺失时显式 raise，
  附 friendly Chinese hint）；`uv run mj-agent check` 命令 provider-aware
  探测 — manual 验 missing-key 错误输出。当前无 automated BDD coverage。
- **升级触发条件**: M3 pytest-bdd step defs 实装 + LLM provider config mock
  harness（设 `ARK_API_KEY=""` + `LLM_API_KEY=""` 验 `LLMConfigError` raise）。
- **预计时间**: M3 EOL（per Phase M3 BDD 集中实装节奏）。

### G22/G21 Justification: Local provider constructs ChatOpenAI without extra_body.thinking

- **REQ**: REQ-002 / **Risk**: high / **Adapter**: python / **ADR-027**
- **原因**: M1 baseline + ADR-027 phased rollout（vLLM/SGLang/Ollama 不接受
  `thinking` 参数 — 传入会 422；Ark DeepSeek V3 接受）；BDD 层验证推迟 M3。
- **替代验证手段**: `make_llm()` 中 provider 分支已实装（`local-openai-compat`
  分支构造 ChatOpenAI 时**不**传 `extra_body.thinking`，仅 ark 分支传）；
  DGX-Spark 端点 manual smoke 通过 `/mj-agent-infra-llm-endpoint-probe`
  (3-step probe: reachable + model id match + 1-token chat smoke)。
- **升级触发条件**: M3 pytest-bdd step defs + `local-openai-compat` provider
  mock harness（验 ChatOpenAI 构造时 `extra_body` 字段不含 `thinking` key）。
- **预计时间**: M3 EOL（per Phase M3 BDD 集中实装节奏）。

### G22/G21 Justification: effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY is empty ★ post M-FU#1 fix

- **REQ**: REQ-003 / **Risk**: high / **Adapter**: python
- **原因**: M1 baseline + ADR-027 sentinel 设计 edge case（vLLM-like endpoints
  接受 `"EMPTY"` 字串作 placeholder key；Ark 不接受 → 区分 provider 行为）；
  BDD 层 step defs 推迟 M3。Post PR #195 M-FU#1 trace.yml quote fix 后,该
  scenario 正确进入 G22/G21 filter scope。
- **替代验证手段**: `src/mj_agent/config.py` 中 `effective_llm_api_key`
  property 已实装（若 `LLM_API_KEY` 为空且 `LLM_PROVIDER=local-openai-compat`
  → 返回 `"EMPTY"` 字串；否则返回原值或触发 ark 分支错误）。Manual config
  测试覆盖该 sentinel 路径。
- **升级触发条件**: M3 pytest-bdd step defs + config edge-case test harness
  （验 sentinel 字串 vs 真实 key vs 空字串 3 路径）。
- **预计时间**: M3 EOL（per Phase M3 BDD 集中实装节奏）。

---

> Phase M1 baseline.
