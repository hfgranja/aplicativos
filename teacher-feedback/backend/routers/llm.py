from fastapi import APIRouter
from services.llm_service import check_ollama_status

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
def llm_status():
    return check_ollama_status()
