from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django.conf import settings

from .llm_usage import get_usage_snapshot
from .openai_usage import fetch_openai_usage
from .permissions import IsAdminRole
from .serializers import LlmUsageSerializer


@api_view(["GET"])
@permission_classes([IsAdminRole])
def get_llm_usage(request):
    snapshot = fetch_openai_usage(settings.OPENAI_API_KEY) or get_usage_snapshot()
    total_budget = max(settings.OPENAI_TOKEN_BUDGET, 0)
    used_tokens = snapshot.total_tokens
    remaining_tokens = max(total_budget - used_tokens, 0)
    payload = {
        "provider": "ChatGPT",
        "model": settings.OPENAI_MODEL,
        "total_tokens": total_budget,
        "used_tokens": used_tokens,
        "remaining_tokens": remaining_tokens,
        "prompt_tokens": snapshot.prompt_tokens,
        "completion_tokens": snapshot.completion_tokens,
        "last_updated": snapshot.updated_at,
    }
    return Response(LlmUsageSerializer(payload).data)
