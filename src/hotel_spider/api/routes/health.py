from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def api_health() -> dict[str, str]:
    return {"status": "ok"}
