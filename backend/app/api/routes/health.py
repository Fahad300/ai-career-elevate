from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_class=JSONResponse)
def get_health() -> dict:
    return {"status": "ok"}