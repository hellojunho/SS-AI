import json
from uuid import uuid4

from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .errors import AppError
from .models import BackgroundJob, Quiz, QuizAnswer, QuizQuestion, User, WrongQuestion
from .permissions import IsAdminRole, IsAuthenticatedJWT
from .quiz_logic import (
    admin_quiz_response,
    delete_quiz_records,
    generate_quiz_for_user,
    is_similar_question,
    normalize_question_text,
    parse_choices,
    quiz_to_response,
    shuffle_question_choices,
    stringify_list,
)
from .serializers import (
    AdminQuizGenerateRequestSerializer,
    AdminQuizUpdateSerializer,
    QuizAnswerCreateSerializer,
)
from .tasks import run_admin_generate_all, run_admin_generate_quiz


def _error_response(exc: AppError) -> Response:
    return Response({"detail": exc.detail}, status=exc.status_code)


def _get_current_id(request):
    value = request.query_params.get("current_id")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@api_view(["POST"])
@permission_classes([IsAdminRole])
def generate_quiz_from_summary(request):
    current_user = request.user
    try:
        quiz = generate_quiz_for_user(current_user)
        payload = quiz_to_response(quiz, current_user=current_user)
        return Response(payload)
    except AppError as exc:
        return _error_response(exc)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_generate_quiz(request):
    serializer = AdminQuizGenerateRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    target_user = User.objects.filter(user_id=serializer.validated_data["user_id"]).first()
    if not target_user:
        return Response({"detail": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    job_id = uuid4().hex
    BackgroundJob.objects.create(
        job_id=job_id,
        job_type=BackgroundJob.JOB_TYPE_QUIZ_GENERATE,
        status=BackgroundJob.STATUS_PENDING,
        progress=0,
    )
    run_admin_generate_quiz.delay(job_id, target_user.user_id, request.user.id)
    return Response({"job_id": job_id})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_generate_all(request):
    job_id = uuid4().hex
    BackgroundJob.objects.create(
        job_id=job_id,
        job_type=BackgroundJob.JOB_TYPE_QUIZ_GENERATE_ALL,
        status=BackgroundJob.STATUS_PENDING,
        progress=0,
    )
    run_admin_generate_all.delay(job_id)
    return Response({"job_id": job_id})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_generate_status(request, job_id: str):
    job = BackgroundJob.objects.filter(job_id=job_id).first()
    if not job:
        return Response({"detail": "작업을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    payload = {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
    }
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_list_quizzes(request):
    quizzes = Quiz.objects.select_related("user").prefetch_related("questions").order_by("-created_at")
    results: list[dict] = []
    for quiz in quizzes:
        try:
            source_user_id = quiz.user.user_id if quiz.user else ""
            results.append(admin_quiz_response(quiz, source_user_id))
        except AppError:
            continue
    return Response(results)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdminRole])
def admin_quiz_detail(request, quiz_id: int):
    quiz = Quiz.objects.select_related("user").prefetch_related("questions").filter(id=quiz_id).first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        source_user_id = quiz.user.user_id if quiz.user else ""
        try:
            return Response(admin_quiz_response(quiz, source_user_id))
        except AppError as exc:
            return _error_response(exc)

    if request.method == "PATCH":
        serializer = AdminQuizUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        question = quiz.questions.order_by("id").first()
        if not question:
            return Response({"detail": "퀴즈 문항을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if "title" in payload:
            quiz.title = payload["title"]
        if "link" in payload:
            quiz.link = payload["link"]
        if "question" in payload:
            question.question = payload["question"]
        if "choices" in payload:
            question.choices = stringify_list(payload["choices"]) or "[]"
        if "correct" in payload:
            question.correct = payload["correct"]
        if "wrong" in payload:
            question.wrong = stringify_list(payload["wrong"]) or "[]"
        if "explanation" in payload:
            question.explanation = payload["explanation"]
        if "reference" in payload:
            question.reference = payload["reference"]

        with transaction.atomic():
            quiz.save()
            question.save()

        source_user_id = quiz.user.user_id if quiz.user else ""
        try:
            return Response(admin_quiz_response(quiz, source_user_id))
        except AppError as exc:
            return _error_response(exc)

    delete_quiz_records(quiz)
    return Response({"deleted": quiz_id})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_mix_quiz_choices(request, quiz_id: int):
    quiz = Quiz.objects.select_related("user").prefetch_related("questions").filter(id=quiz_id).first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    question = quiz.questions.order_by("id").first()
    if not question:
        return Response({"detail": "퀴즈 문항을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    if not shuffle_question_choices(question):
        return Response({"detail": "섞을 선택지가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

    response = quiz_to_response(quiz, current_user=request.user)
    source_user_id = quiz.user.user_id if quiz.user else ""
    return Response({**response, "source_user_id": source_user_id})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_mix_all_quiz_choices(request):
    quizzes = Quiz.objects.prefetch_related("questions").all()
    mixed = 0
    for quiz in quizzes:
        question = quiz.questions.order_by("id").first()
        if not question:
            continue
        if shuffle_question_choices(question):
            mixed += 1
    return Response({"mixed": mixed})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_dedupe_quizzes(request):
    quizzes = Quiz.objects.prefetch_related("questions").order_by("created_at")
    kept_questions: list[str] = []
    removed_ids: list[int] = []

    for quiz in quizzes:
        question = quiz.questions.order_by("id").first()
        if not question:
            continue
        question_text = normalize_question_text(question.question)
        if not question_text:
            continue
        if any(is_similar_question(existing, question_text) for existing in kept_questions):
            removed_ids.append(quiz.id)
            delete_quiz_records(quiz)
            continue
        kept_questions.append(question_text)

    return Response({"removed": len(removed_ids), "removed_ids": removed_ids, "kept": len(kept_questions)})


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def latest_quiz(request):
    current_user = request.user
    quiz = Quiz.objects.filter(user=current_user).order_by("-created_at").first()
    if not quiz:
        quiz = Quiz.objects.order_by("-created_at").first()
        if not quiz:
            return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(quiz_to_response(quiz, current_user=current_user, scope="all"))
        except AppError as exc:
            return _error_response(exc)

    try:
        return Response(quiz_to_response(quiz, current_user=current_user, scope="user"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def first_quiz_all(request):
    quiz = Quiz.objects.order_by("created_at").first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="all"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def latest_quiz_all(request):
    quiz = Quiz.objects.order_by("-created_at").first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="all"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def next_quiz(request):
    current_id = _get_current_id(request)
    if current_id is None:
        return Response({"detail": "current_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    quiz = Quiz.objects.filter(user=request.user, id__gt=current_id).order_by("id").first()
    if not quiz:
        return Response({"detail": "다음 퀴즈가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="user"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def next_quiz_all(request):
    current_id = _get_current_id(request)
    if current_id is None:
        return Response({"detail": "current_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    quiz = Quiz.objects.filter(id__gt=current_id).order_by("id").first()
    if not quiz:
        return Response({"detail": "다음 퀴즈가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="all"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def prev_quiz(request):
    current_id = _get_current_id(request)
    if current_id is None:
        return Response({"detail": "current_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    quiz = Quiz.objects.filter(user=request.user, id__lt=current_id).order_by("-id").first()
    if not quiz:
        return Response({"detail": "이전 퀴즈가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="user"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def prev_quiz_all(request):
    current_id = _get_current_id(request)
    if current_id is None:
        return Response({"detail": "current_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    quiz = Quiz.objects.filter(id__lt=current_id).order_by("-id").first()
    if not quiz:
        return Response({"detail": "이전 퀴즈가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user, scope="all"))
    except AppError as exc:
        return _error_response(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def quiz_summary(request):
    scope = request.query_params.get("scope", "user")
    current_user = request.user

    if scope not in {"user", "all"}:
        return Response({"detail": "잘못된 범위입니다."}, status=status.HTTP_400_BAD_REQUEST)

    quiz_scope = Quiz.objects.all()
    if scope == "user":
        quiz_scope = quiz_scope.filter(user=current_user)

    total_count = quiz_scope.count()
    if total_count == 0:
        return Response({"total_count": 0, "correct_count": 0, "wrong_count": 0, "accuracy_rate": 0.0})

    question_scope = QuizQuestion.objects.filter(quiz__in=quiz_scope)

    first_answer_subquery = QuizAnswer.objects.filter(
        question_id=OuterRef("pk"),
        user=current_user,
    ).order_by("created_at").values("id")[:1]

    first_answer_ids = [
        value
        for value in question_scope.annotate(first_answer_id=Subquery(first_answer_subquery)).values_list("first_answer_id", flat=True)
        if value is not None
    ]

    correct_count = QuizAnswer.objects.filter(id__in=first_answer_ids, is_correct=True).count()
    wrong_count = QuizAnswer.objects.filter(id__in=first_answer_ids, is_wrong=True).count()
    accuracy_rate = round((correct_count / total_count) * 100, 1)

    return Response(
        {
            "total_count": total_count,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "accuracy_rate": accuracy_rate,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def wrong_notes(request):
    current_user = request.user
    wrong_entries = (
        WrongQuestion.objects.filter(solver_user=current_user)
        .select_related("question__quiz")
        .order_by(F("last_solved_at").desc(nulls_last=True))
    )

    results: list[dict] = []
    for entry in wrong_entries:
        question = entry.question
        if not question:
            continue
        quiz = getattr(question, "quiz", None)
        results.append(
            {
                "quiz_id": question.quiz_id,
                "question_id": question.id,
                "question": question.question,
                "choices": parse_choices(question.choices),
                "correct": question.correct,
                "wrong": parse_choices(question.wrong),
                "explanation": question.explanation,
                "reference": question.reference,
                "link": quiz.link if quiz else "",
            }
        )

    return Response(results)


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def get_quiz(request, quiz_id: int):
    quiz = Quiz.objects.filter(id=quiz_id, user=request.user).first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(quiz_to_response(quiz, current_user=request.user))
    except AppError as exc:
        return _error_response(exc)


@api_view(["POST"])
@permission_classes([IsAuthenticatedJWT])
def submit_quiz_answer(request, quiz_id: int):
    serializer = QuizAnswerCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    quiz = Quiz.objects.prefetch_related("questions").filter(id=quiz_id).first()
    if not quiz:
        return Response({"detail": "퀴즈를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    question = quiz.questions.order_by("id").first()
    if not question:
        return Response({"detail": "퀴즈 문항을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    normalized_answer = serializer.validated_data["answer"].strip()
    is_correct = normalized_answer == question.correct.strip()
    is_wrong = not is_correct

    with transaction.atomic():
        QuizAnswer.objects.create(
            question=question,
            user=request.user,
            answer_text=normalized_answer,
            is_correct=is_correct,
            is_wrong=is_wrong,
        )

        now = timezone.now()
        quiz.tried_at = now
        if is_correct:
            quiz.solved_at = now
        quiz.save(update_fields=["tried_at", "solved_at"] if is_correct else ["tried_at"])

        if is_wrong:
            wrong_record = WrongQuestion.objects.filter(
                question=question,
                solver_user=request.user,
            ).first()
            if wrong_record:
                try:
                    history = json.loads(wrong_record.user_answers)
                except json.JSONDecodeError:
                    history = []
                history.append(normalized_answer)
                wrong_record.user_answers = json.dumps(history, ensure_ascii=False)
                wrong_record.last_solved_at = now
                wrong_record.save(update_fields=["user_answers", "last_solved_at"])
            else:
                WrongQuestion.objects.create(
                    question=question,
                    question_creator=quiz.user,
                    solver_user=request.user,
                    correct_answer=question.correct,
                    wrong_answer=question.wrong,
                    reference_link=question.reference,
                    user_answers=json.dumps([normalized_answer], ensure_ascii=False),
                    last_solved_at=now,
                )

    answer_history = QuizAnswer.objects.filter(
        question=question,
        user=request.user,
    ).order_by("created_at")

    history_values = [answer.answer_text for answer in answer_history]
    has_correct_attempt = any(answer.is_correct for answer in answer_history)
    has_wrong_attempt = any(answer.is_wrong for answer in answer_history)

    return Response(
        {
            "quiz_id": quiz.id,
            "question_id": question.id,
            "answer": normalized_answer,
            "is_correct": is_correct,
            "is_wrong": is_wrong,
            "has_correct_attempt": has_correct_attempt,
            "has_wrong_attempt": has_wrong_attempt,
            "answer_history": history_values,
            "tried_at": quiz.tried_at,
            "solved_at": quiz.solved_at,
        }
    )
