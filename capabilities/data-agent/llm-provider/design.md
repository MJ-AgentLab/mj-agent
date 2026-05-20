---
type: capability-design
capability: data-agent.llm-provider
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Design: LLM Provider Abstraction

> Phase M1 baseline (≤ 200 lines per R-G3). Per ADR-027.

## §1 Context

mj-agent is a LangChain-based agent; LLM access is via `ChatOpenAI` (LangChain
openai integration). Two operational needs require an abstraction layer:

1. **Default cloud LLM** (Volcengine Ark + DeepSeek V3) for analyst questions
   over biz data; includes private `extra_body.thinking` knob to toggle DeepSeek
   V3's chain-of-thought mode
2. **Local LLM endpoint** (DGX-Spark host running vLLM / SGLang / Ollama) for
   data-sensitive scenarios where cloud egress is not acceptable, or for cost
   experimentation; OpenAI-compatible API but **rejects** Ark's `extra_body.thinking` (returns 422)

**Threats**：

1. Default cloud LLM accidentally used in "no cloud egress" deployment → data exfiltration via LLM
2. `extra_body.thinking` sent to local endpoint → 422 error breaks user experience
3. Hard-coded API key in code → secret in git
4. Lazy fallback to `ark_*` env vars when generic `llm_*` env vars empty → confusing dual config
5. `make_llm()` raised at import time → test fixtures can't construct Settings in empty .env

**Non-threats** (out of scope here, governed elsewhere)：
- Endpoint reachability monitoring → `/mj-agent-infra-llm-endpoint-probe` skill
- Rate limiting → ChatOpenAI's `max_retries=2` + endpoint provider's own limits
- Cost tracking → not implemented; future capability

## §2 Decision

**Provider-branching factory function + cached_property fallback chains + lazy validation**.

| Component | File | Purpose |
|---|---|---|
| Factory | `src/mj_agent/llm.py:make_llm()` | Branches on `settings.llm_provider`; returns `ChatOpenAI` |
| Config | `src/mj_agent/config.py` | 8 LLM-related Settings fields + 2 cached_property helpers |
| Error | `src/mj_agent/llm.py:LLMConfigError(RuntimeError)` | Raised at make_llm call time (lazy validation; Settings stays constructible) |
| CLI health | `src/mj_agent/server/cli.py:check` | Provider-aware credential validation (no endpoint contact) |
| Endpoint probe | `.claude/skills/mj-agent-infra-llm-endpoint-probe/` | 3-step probe (reachable + model id + 1-token chat) — out-of-scope here |

**Why lazy validation (LLMConfigError at make_llm time, not Settings construction)**：

- Settings construction happens at module import → import-time errors break test fixtures that don't actually need LLM
- Graph build time (`make_graph()`) is the natural validation point — that's where LLM access is required
- Trade-off: errors surface "later" than possible; but consistency with LangGraph's lazy graph compile is more important

**Why `"EMPTY"` sentinel for local provider**：

- vLLM / SGLang / Ollama default to "no api key required"; they accept any non-empty string
- ChatOpenAI requires `api_key` to be set (raises its own error on empty)
- `"EMPTY"` is a documented vLLM convention; passes ChatOpenAI's check + works with local endpoints

**Why NO `extra_body.thinking` for local provider**：

- DeepSeek V3 `extra_body.thinking={"type":"enabled"|"disabled"}` is Volcengine Ark private; not part of OpenAI API spec
- vLLM / SGLang / Ollama reject unknown `extra_body` keys with 422
- Setting `extra_body={}` would still differ from "no extra_body kwarg passed" (LangChain might serialize); safer to omit kwarg entirely

## §3 Architecture

```
[Settings construction at import time]   ──── config.py Settings class
       │
       ├─► llm_provider: Literal["ark", "local-openai-compat"]
       │   (pydantic ValidationError if other value)
       │
       ├─► llm_base_url / llm_api_key / llm_model_id / llm_thinking_enabled
       │   / llm_timeout_sec  (new generic)
       │
       └─► ark_base_url / ark_api_key  (legacy back-compat)

[Graph build time]                       ──── agent.py:make_graph()
       │
       ▼
[make_llm()]                              ──── llm.py
       │
       ├──► branch on settings.llm_provider
       │
       ├──► "ark" path:
       │     ├─► effective_llm_api_key  (llm_api_key OR ark_api_key)
       │     ├─► raise LLMConfigError if both empty
       │     ├─► effective_llm_base_url  (llm_base_url OR ark_base_url)
       │     └─► return ChatOpenAI(..., extra_body={"thinking": {"type": <mode>}})
       │
       └──► "local-openai-compat" path:
             ├─► raise LLMConfigError if llm_base_url empty (NO ark fallback)
             ├─► effective_llm_api_key  (llm_api_key OR "EMPTY" sentinel)
             └─► return ChatOpenAI(..., base_url=llm_base_url)  # NO extra_body

[mj-agent check]                          ──── cli.py
       │
       └──► provider-aware credential validation only (NO endpoint contact)
            ├─► ark: check ARK_API_KEY or LLM_API_KEY → failures.append
            ├─► local: check LLM_BASE_URL → failures.append (with vLLM example)
            └─► success output: "llm provider = <name> (endpoint=<url>)"

[Endpoint probe]                          ──── .claude/skills/mj-agent-infra-llm-endpoint-probe
       │  (out of scope of this capability)
       │
       └──► 3-step probe: reachable + model id + 1-token chat
```

**Cross-capability dependencies (2 outbound)**：

- `infrastructure.docker-compose`：LLM env vars (`LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` / `ARK_API_KEY`) injected per profile via compose `env_file: ../../.env`; secrets resolution owned by docker-compose capability
- `infrastructure.mcp-server-governance`：`.mcp.json` ssh-manager has DGX-Spark host entry; `local-openai-compat` endpoint typically lives on the same DGX host (192.168.0.189); trust posture coordination expected

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **A. Factory function with explicit branching (chosen)** | Simple; one file owns provider logic | Adding 3rd provider grows the function | 2 providers expected for foreseeable future; if 3rd needed, refactor to dispatch dict |
| B. Plugin-style provider registry | Extensible to many providers | Over-engineered for 2 cases | Rejected — YAGNI |
| **C. Lazy `LLMConfigError` at make_llm time (chosen)** | Settings safe in empty .env; test fixtures unblocked | Errors surface later than possible | Consistency with LangGraph lazy compile + test ergonomics outweigh |
| D. Eager validation at Settings construction | Errors at import time | Breaks `import mj_agent.config` in empty .env | Rejected — fixture friction |
| **E. `"EMPTY"` sentinel for local api_key (chosen)** | Works with vLLM/Ollama no-auth default; passes ChatOpenAI check | Magic string; potentially confusing | vLLM convention; documented in code comment |
| F. Pass `api_key=None` | Cleaner intent | ChatOpenAI raises | Rejected by library |
| **G. Omit `extra_body` kwarg entirely for local (chosen)** | Safe — never sends Ark-private params | Slight asymmetry between branches | Empty dict still serialized differently by LangChain; safer omission |
| H. Always pass `extra_body={}` for local | Symmetry | Library may or may not strip | Rejected — defensive |

## §5 Open Questions

1. **`temperature=0.7 / max_retries=2` as contract or impl detail?** Duplicated
   across both branches. Contract-locking might over-constrain; leaving as impl
   detail risks drift between providers. Phase M2 decision.

2. **`effective_llm_api_key` returning `"EMPTY"` for ark provider** — impossible
   today (ark branch uses `or self.ark_api_key.get_secret_value()` not `or "EMPTY"`)
   but the cached_property is shared. Should the helper be provider-split for
   clarity?

3. **`LLMConfigError` raised at call time** — test fixtures relying on Settings
   instantiation (e.g. `tests/conftest.py`) currently work in empty .env. REQ-003
   should explicitly capture this lazy-validation semantic as a contract.

4. **`Profile` enum invariance** — ADR-027 explicitly keeps `Profile = Literal["dev","test","prod"]` (no `dgx`). DGX is "purely an LLM endpoint switch
   orthogonal to MJ_CONFIG_PROFILE". REQ-003 currently doesn't enforce this
   invariance — should it? Out of scope today; tracked as Phase 2+ refactor.

> Phase M2 will fill in adapter §BDD Rules + §TDD Rules per
> `sdd/adapters/{python,bdd-tdd}.md`.
