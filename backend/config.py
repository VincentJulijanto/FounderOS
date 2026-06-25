from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # === QwenCloud (OpenAI-compatible) — paste key in .env when ready ===
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # === MCP tool server — paste URL in .env when ready ===
    mcp_server_url: str = ""

    # === Database ===
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/founderos"

    # === App ===
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    # === Mock flag — True by default; auto-stays True if no key present ===
    # Set USE_MOCK_LLM=false in .env once QWEN_API_KEY is filled in.
    use_mock_llm: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_live(self) -> bool:
        """True only when a key is present and mock mode is explicitly disabled."""
        return bool(self.qwen_api_key) and not self.use_mock_llm


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
