from pathlib import Path
from uuid import uuid4

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import BackgroundJob
from .permissions import IsAdminRole
from .serializers import LearnStatusSerializer, WebDocumentPayloadSerializer
from .tasks import DOCS_FOLDERS, DOCS_ROOT, DOCS_WEB_URLS, run_docs_learning_job


def _ensure_docs_dirs() -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in DOCS_FOLDERS.values():
        (DOCS_ROOT / folder).mkdir(parents=True, exist_ok=True)
    (DOCS_ROOT / "web").mkdir(parents=True, exist_ok=True)
    DOCS_WEB_URLS.touch(exist_ok=True)


@api_view(["POST"])
@permission_classes([IsAdminRole])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    _ensure_docs_dirs()

    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"detail": "파일이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    suffix = Path(file_obj.name).suffix.lower()
    target_folder = DOCS_FOLDERS.get(suffix)
    if not target_folder:
        return Response({"detail": "지원하지 않는 확장자입니다."}, status=status.HTTP_400_BAD_REQUEST)

    destination = DOCS_ROOT / target_folder / file_obj.name
    with destination.open("wb") as out:
        for chunk in file_obj.chunks():
            out.write(chunk)

    return Response({"filename": destination.name, "stored_in": str(destination)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def upload_web_document(request):
    _ensure_docs_dirs()

    serializer = WebDocumentPayloadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    url = serializer.validated_data["url"]
    with DOCS_WEB_URLS.open("a", encoding="utf-8") as file:
        file.write(f"{url}\n")

    return Response({"stored_url": url}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def start_learning(request):
    running = BackgroundJob.objects.filter(
        job_type=BackgroundJob.JOB_TYPE_DOCS_LEARN,
        status=BackgroundJob.STATUS_RUNNING,
    ).exists()
    if running:
        return Response({"detail": "학습이 이미 진행 중입니다."}, status=status.HTTP_409_CONFLICT)

    job_id = uuid4().hex
    BackgroundJob.objects.create(
        job_id=job_id,
        job_type=BackgroundJob.JOB_TYPE_DOCS_LEARN,
        status=BackgroundJob.STATUS_RUNNING,
        progress=0,
        message="학습을 준비하고 있습니다.",
    )
    run_docs_learning_job.delay(job_id)
    return Response({"message": "학습을 시작했습니다."}, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def get_learning_status(request):
    latest = (
        BackgroundJob.objects.filter(job_type=BackgroundJob.JOB_TYPE_DOCS_LEARN)
        .order_by("-created_at")
        .first()
    )
    if not latest:
        payload = {"status": "idle", "progress": 0, "message": "대기 중"}
    else:
        payload = {
            "status": latest.status,
            "progress": latest.progress,
            "message": latest.message or "",
        }
    return Response(LearnStatusSerializer(payload).data)
