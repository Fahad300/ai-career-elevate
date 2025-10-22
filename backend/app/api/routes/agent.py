from fastapi import APIRouter

router = APIRouter(prefix="/agent", tags=["agent"]) 

@router.get("")
def placeholder_agent() -> dict:
    return {"ok": True}