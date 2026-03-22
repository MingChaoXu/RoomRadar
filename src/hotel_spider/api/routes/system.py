from pathlib import Path

from fastapi import APIRouter

from hotel_spider.core.config import get_settings

router = APIRouter()


@router.get("/runtime")
def runtime_info() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_env": settings.app_env,
        "amap_provider": settings.amap_provider,
        "amap_mcp_command": settings.amap_mcp_command,
        "amap_mcp_args": settings.amap_mcp_args,
        "amap_mcp_enabled": settings.amap_provider == "mcp",
        "amap_api_key_configured": bool(settings.amap_maps_api_key),
        "ctrip_provider": settings.ctrip_provider,
        "ctrip_headless": settings.ctrip_headless,
        "ctrip_storage_state_configured": bool(settings.ctrip_storage_state_path),
        "ctrip_storage_state_exists": bool(
            settings.ctrip_storage_state_path and Path(settings.ctrip_storage_state_path).exists()
        ),
        "playwright_browsers_path": settings.playwright_browsers_path,
    }
