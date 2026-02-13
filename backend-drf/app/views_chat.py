from datetime import datetime
from pathlib import Path

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import ChatRecord, ChatSummary
from .permissions import IsAuthenticatedJWT
from .serializers import ChatRequestSerializer
from .services import generate_chat_answer, sanitize_chat_text, summarize_chat

BASE_DIR = Path(__file__).resolve().parents[1]
RECORD_DIR = BASE_DIR / "chat" / "record"
SUMMARY_DIR = BASE_DIR / "chat" / "summation"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_chat_file(file_path: Path) -> list[dict]:
    entries: list[dict] = []
    if not file_path.exists():
        return entries

    for line in file_path.read_text(encoding="utf-8").splitlines():
        content = line.strip()
        if not content:
            continue
        if content.startswith("나: "):
            entries.append({"role": "me", "content": content[3:]})
        elif content.startswith("GPT: "):
            entries.append({"role": "gpt", "content": content[5:]})
        elif content.startswith("출처: ") and entries and entries[-1]["role"] == "gpt":
            entries[-1]["content"] = f"{entries[-1]['content']}\n{content}"
        elif entries:
            entries[-1]["content"] = f"{entries[-1]['content']}\n{content}"

    for entry in entries:
        if entry["role"] == "gpt":
            entry["content"] = sanitize_chat_text(entry["content"])
    return entries


def _list_chat_dates(user_id: str) -> list[str]:
    user_dir = RECORD_DIR / user_id
    if not user_dir.exists():
        return []

    dates: list[str] = []
    for file_path in user_dir.glob(f"{user_id}-*.txt"):
        name = file_path.stem
        date_str = name.replace(f"{user_id}-", "", 1)
        if date_str:
            dates.append(date_str)
    return sorted(dates, reverse=True)


def _current_date_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


@api_view(["POST"])
@permission_classes([IsAuthenticatedJWT])
def ask_chat(request):
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    message = serializer.validated_data["message"]
    try:
        answer, reference = generate_chat_answer(message)
    except Exception:
        return Response({"detail": "ChatGPT 응답을 불러오지 못했습니다."}, status=status.HTTP_502_BAD_GATEWAY)

    date_str = _current_date_str()
    user = request.user
    user_dir = RECORD_DIR / user.user_id
    _ensure_dir(user_dir)
    file_path = user_dir / f"{user.user_id}-{date_str}.txt"

    with file_path.open("a", encoding="utf-8") as file:
        file.write(f"나: {message}\n")
        file.write(f"GPT: {answer}\n")
        if reference:
            file.write(f"출처: {reference}\n")
        file.write("\n")

    ChatRecord.objects.create(user=user, file_path=str(file_path))
    return Response({"answer": answer, "reference": reference, "file_path": str(file_path)})


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def get_chat_history_dates(request):
    user = request.user
    return Response({"dates": _list_chat_dates(user.user_id), "today": _current_date_str()})


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def get_chat_history(request, date_str: str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return Response({"detail": "날짜 형식이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user_dir = RECORD_DIR / user.user_id
    file_path = user_dir / f"{user.user_id}-{date_str}.txt"
    today = _current_date_str()

    if not file_path.exists():
        if date_str == today:
            return Response({"date": date_str, "entries": [], "is_today": True})
        return Response({"detail": "대화 기록이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    entries = _parse_chat_file(file_path)
    return Response({"date": date_str, "entries": entries, "is_today": date_str == today})


@api_view(["POST"])
@permission_classes([IsAuthenticatedJWT])
def summarize_day(request):
    user = request.user
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")

    user_record_dir = RECORD_DIR / user.user_id
    record_file = user_record_dir / f"{user.user_id}-{date_str}.txt"
    if not record_file.exists():
        return Response({"detail": "대화 기록이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    content = record_file.read_text(encoding="utf-8")
    summary = summarize_chat(content, now)

    user_summary_dir = SUMMARY_DIR / user.user_id
    _ensure_dir(user_summary_dir)
    summary_file = user_summary_dir / f"{user.user_id}-{date_str}_sum.txt"
    summary_file.write_text(summary, encoding="utf-8")

    ChatSummary.objects.create(user=user, file_path=str(summary_file), summary_date=now)
    return Response({"file_path": str(summary_file), "summary": summary})
