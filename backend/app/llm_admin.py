from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .auth import require_admin
from .config import settings
from .llm_usage import get_usage_snapshot
from .openai_usage import fetch_openai_usage


class LlmUsageResponse(BaseModel):
    provider: str
    model: str
    total_tokens: int
    used_tokens: int
    remaining_tokens: int
    prompt_tokens: int
    completion_tokens: int
    last_updated: datetime | None


router = APIRouter(prefix="/admin/llm", tags=["admin-llm"])


@router.get("/usage", response_model=LlmUsageResponse)
def get_llm_usage(current_user=Depends(require_admin)):
    snapshot = fetch_openai_usage(settings.openai_api_key) or get_usage_snapshot()
    total_budget = max(settings.openai_token_budget, 0)
    used_tokens = snapshot.total_tokens
    remaining_tokens = max(total_budget - used_tokens, 0)
    return LlmUsageResponse(
        provider="ChatGPT",
        model=settings.openai_model,
        total_tokens=total_budget,
        used_tokens=used_tokens,
        remaining_tokens=remaining_tokens,
        prompt_tokens=snapshot.prompt_tokens,
        completion_tokens=snapshot.completion_tokens,
        last_updated=snapshot.updated_at,
    )
