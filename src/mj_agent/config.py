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

    @field_validator("biz_allowed_schemas", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

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
