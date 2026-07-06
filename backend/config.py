from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of launch directory
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), case_sensitive=False)

    # === QwenCloud (OpenAI-compatible) — paste key in .env when ready ===
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # === MCP tool server — paste URL in .env when ready ===
    mcp_server_url: str = ""

    # === Database (off-path — vault is the only persistence layer, Decision #1) ===
    database_url: str = "postgresql+asyncpg://localhost:5432/founderos"

    # === App ===
    app_env: str = "development"
    # CORS allow-list. ALLOWED_ORIGINS is the pivot/Decision-#8 name; cors_origins
    # is kept as a fallback so older .env files still work.
    allowed_origins: str = ""
    cors_origins: str = "http://localhost:3000"

    # === Vault (Decision #1) — per-company markdown vault root, env-configurable. ===
    vault_path: str = "./vault"

    # === Mock flag — True by default; auto-stays True if no key present ===
    # Set USE_MOCK_LLM=false in .env once QWEN_API_KEY is filled in.
    use_mock_llm: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.allowed_origins or self.cors_origins
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_live(self) -> bool:
        """True only when a key is present and mock mode is explicitly disabled."""
        return bool(self.qwen_api_key) and not self.use_mock_llm


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
