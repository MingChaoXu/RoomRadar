from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "hotel-spider"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/hotel_spider.db"
    provider_mode: str = "mock"
    amap_provider: str = "mock"
    amap_mcp_command: str = "uvx"
    amap_mcp_args: str = "amap-mcp-server"
    amap_maps_api_key: str | None = None
    amap_mcp_timeout_seconds: float = 20.0
    amap_hotel_keyword: str = "酒店"
    playwright_browsers_path: str | None = None
    ctrip_provider: str = "mock"
    ctrip_storage_state_path: str | None = None
    ctrip_headless: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
