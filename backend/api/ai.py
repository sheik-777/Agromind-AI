from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.auth.deps import get_current_user_optional
from backend.models.models import User
from backend.services.ai_orchestrator import (
    answer_with_conversation,
    field_context,
)
from backend.services.llm_client import llm_status

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatMessage(BaseModel):
    role: str
    content: str


class AskIn(BaseModel):
    question: str
    image_quality: Optional[str] = None
    conversation: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None


@router.post("/ask")
async def ask(
    payload: AskIn,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    q = payload.question.strip()
    if not q:
        raise HTTPException(400, "Question is required")
    if len(q) > 4000:
        raise HTTPException(400, "Question too long (max 4000 characters)")

    ctx = field_context(current_user, db)

    conversation = None
    if payload.conversation:
        conversation = [{"role": m.role, "content": m.content} for m in payload.conversation]

    result = await answer_with_conversation(q, ctx, conversation)

    # Backward-compatible fields for existing mobile/web clients
    result["inferred"] = result["answer"]
    result["recommended"] = result["answer"]
    result["field_available"] = result["field_context_used"]
    result["retrieved_knowledge"] = result["sources"]
    result["field_context"] = ctx

    return result


@router.get("/status")
def status():
    return {"llm": llm_status(), "assistant": "AgroMind grounded AI engine ready"}


@router.get("/health")
def health():
    return {"status": "healthy", "llm": llm_status()}