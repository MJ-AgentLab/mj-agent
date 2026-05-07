"""Runtime configuration loaded from .env via pydantic-settings.

Profile-aware: `MJ_CONFIG_PROFILE=dev|test|prod` selects the matching
POSTGRES_{PROFILE}_HOST/PORT pair. Variable naming aligns with mj-system so
that a merged .env works in co-deployment (ADR-008).
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

    # ── 2. LLM Provider (Volcengine Ark, OpenAI-compatible) ───────────
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
    # a dedicated mj-agent postgres container. Defaults fall back to
    # localhost:5432 so non-Docker dev still works (point them at any
    # local postgres you own).
    mj_agent_memory_host: str = "localhost"
    mj_agent_memory_port: int = 5432
    mj_agent_memory_db: str = "mj_agent_memory"
    mj_agent_memory_user: str = ""
    mj_agent_memory_password: SecretStr = SecretStr("")
    mj_agent_memory_pool_max: int = 10

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
