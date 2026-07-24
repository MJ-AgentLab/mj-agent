"""Runtime configuration loaded from .env via pydantic-settings.

Profile-aware: `MJ_CONFIG_PROFILE=dev|test|prod` selects the matching
POSTGRES_{PROFILE}_HOST/PORT pair. Variable naming follows mj-system
convention for **operational consistency** across DEV/TEST/PROD profile
matrix (ADR-008) — **not** to share .env files between projects. mj-agent
is an independent compose project with its own secrets pipeline (separate
secrets.enc + separate team password); biz pg is accessed only as a
consumer via the analyst RO role.
"""

from __future__ import annotations

from functools import cached_property
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Profile = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    """Typed view over environment variables declared in `.env.example`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── 0. Application ────────────────────────────────────────────────
    mj_agent_env: Literal["development", "test", "production"] = "development"
    mj_agent_debug: bool = True
    mj_agent_log_level: str = "info"
    mj_config_profile: Profile = "dev"

    # ── 1. Database ───────────────────────────────────────────────────
    postgres_analyst_user: str = ""
    postgres_analyst_password: SecretStr = SecretStr("")
    postgres_biz_db: str = "mj_system_db"

    postgres_dev_host: str = "localhost"
    postgres_dev_port: int = 5432
    postgres_test_host: str = ""
    postgres_test_port: int = 5432
    postgres_prod_host: str = ""
    postgres_prod_port: int = 5432

    biz_allowed_schemas: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["biz_dws", "biz_dwd"]
    )

    # Table-level allowlist for biz_dwd. mj-system exposes exactly these two
    # dimension tables; everything else in biz_dwd is rejected at L1 guardrail
    # even though the schema is whitelisted. Treats biz_dws as wildcard.
    biz_allowed_dwd_tables: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["dwd_dim_product_interface", "dwd_dim_institution"]
    )

    # ── 2. LLM Provider (multi-provider abstraction; ADR-027) ─────────
    # Provider selection: "ark" (default; Volcengine Ark + DeepSeek V3) reads
    # ark_base_url + ark_api_key; "local-openai-compat" (DGX-Spark vLLM /
    # SGLang / Ollama / TGI / llama.cpp) reads llm_base_url + llm_api_key.
    # See effective_llm_base_url / effective_llm_api_key cached_property
    # for fallback semantics (ark provider falls back to ark_* fields, so
    # legacy .env continues to work without LLM_PROVIDER set).
    llm_provider: Literal["ark", "local-openai-compat"] = "ark"
    llm_base_url: str = ""
    llm_api_key: SecretStr = SecretStr("")

    llm_model_id: str = "deepseek-v3-2-251201"
    llm_thinking_enabled: bool = False
    llm_timeout_sec: int = 120
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_api_key: SecretStr = SecretStr("")

    # ── 3. Observability ──────────────────────────────────────────────
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_project: str = "mj-agent-dev"
    langsmith_api_key: SecretStr | None = None

    # ── 4. Runtime Limits ─────────────────────────────────────────────
    sql_max_rows: int = 500
    sql_statement_timeout_sec: int = 60

    # ── 5. Memory storage (mj-agent-owned) ────────────────────────────
    # Phase 1 sub 1.A introduced the checkpointer; storage-stack PR moves
    # the actual host/port out of POSTGRES_{PROFILE}_* (biz domain) onto
    # a dedicated mj-agent postgres container (host port 5433 -> container
    # 5432, avoiding mj-system's mj-postgres on host 5432). Defaults target
    # the storage-stack topology; override `mj_agent_memory_port` to 5432
    # only if you run a bare-metal postgres directly on host 5432.
    mj_agent_memory_host: str = "localhost"
    mj_agent_memory_port: int = 5433
    mj_agent_memory_db: str = "mj_agent_memory"
    mj_agent_memory_user: str = ""
    mj_agent_memory_password: SecretStr = SecretStr("")
    mj_agent_memory_pool_max: int = 10
    # At-rest desensitization (capability data-agent.memory-checkpointer; ADR-038): when True,
    # execute_sql biz rows are replaced by a per-column count digest at checkpoint-persist time
    # (live conversation untouched — REQ-002). Default-on since #365 AC4-6 (the both-paths on-disk
    # canary + smoke round-trip validated it against mj-agent-postgres). Set
    # MJ_AGENT_MEMORY_REDACT_BIZ_ROWS=false to opt out (reversible, config-only; no data migration).
    mj_agent_memory_redact_biz_rows: bool = True
    # TTL/retention eviction (capability data-agent.memory-checkpointer; ADR-038 mechanism C).
    # OPT-IN + irreversible: 0 disables (default). A positive N means `mj-agent memory-evict` deletes
    # whole checkpoint threads whose newest activity is older than N days (mechanism B's digest is
    # forward-only and does not cover answer-side biz values — this bounds their at-rest lifetime).
    # Default-off because eviction is a hard DELETE, unlike the non-destructive redaction above.
    # There is no in-app scheduler; wire `mj-agent memory-evict` into external cron (see runbook).
    mj_agent_memory_ttl_days: int = 0

    # Redis: container is provisioned in the storage stack but no Python
    # client is wired yet. Settings are declared so future code (session
    # cache / streaming buffers / rate limit) can pick them up without a
    # config migration. Empty host disables — checkpointer / agent ignore.
    mj_agent_redis_host: str = ""
    mj_agent_redis_port: int = 6379
    mj_agent_redis_password: SecretStr = SecretStr("")

    # ── 6. Chainlit UI (Phase 1 sub 1.A) ──────────────────────────────
    chainlit_host: str = "127.0.0.1"
    chainlit_port: int = 8000

    @field_validator("biz_allowed_schemas", "biz_allowed_dwd_tables", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    def is_table_allowed(self, schema: str, table: str) -> bool:
        """Return True if (schema, table) is reachable per the contract.

        biz_dws.* is wildcard-allowed; biz_dwd is restricted to the
        explicit ``biz_allowed_dwd_tables`` list. Schemas outside
        ``biz_allowed_schemas`` are rejected outright.
        """
        s = schema.lower()
        t = table.lower()
        if s not in {x.lower() for x in self.biz_allowed_schemas}:
            return False
        if s == "biz_dwd":
            return t in {x.lower() for x in self.biz_allowed_dwd_tables}
        return True

    @cached_property
    def effective_llm_base_url(self) -> str:
        """Provider-aware LLM endpoint URL.

        For ark provider: prefer the new generic ``llm_base_url`` if set,
        else fall back to the legacy ``ark_base_url`` (preserves back-compat
        for unchanged .env files). For local-openai-compat: ``llm_base_url``
        only — empty raises in make_llm().
        """
        if self.llm_provider == "ark":
            return self.llm_base_url or self.ark_base_url
        return self.llm_base_url

    @cached_property
    def effective_llm_api_key(self) -> str:
        """Provider-aware LLM API key.

        For ark: prefer ``llm_api_key`` if set, else ``ark_api_key``. For
        local-openai-compat: prefer ``llm_api_key``; many local servers
        (vLLM unauthenticated, Ollama default) accept ``"EMPTY"`` as a
        sentinel — return that when no key configured so ChatOpenAI does
        not raise ``OpenAIError: api_key client option must be set``.
        """
        if self.llm_provider == "ark":
            return (
                self.llm_api_key.get_secret_value()
                or self.ark_api_key.get_secret_value()
            )
        return self.llm_api_key.get_secret_value() or "EMPTY"

    @cached_property
    def biz_pg_host(self) -> str:
        return {
            "dev": self.postgres_dev_host,
            "test": self.postgres_test_host,
            "prod": self.postgres_prod_host,
        }[self.mj_config_profile]

    @cached_property
    def biz_pg_port(self) -> int:
        return {
            "dev": self.postgres_dev_port,
            "test": self.postgres_test_port,
            "prod": self.postgres_prod_port,
        }[self.mj_config_profile]


settings = Settings()
