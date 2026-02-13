import json
import random
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable

from django.db import transaction
from django.utils import timezone

from .errors import AppError
from .models import (
    ChatSummary,
    Quiz,
    QuizAnswer,
    QuizCorrect,
    QuizQuestion,
    QuizWrong,
    User,
    WrongQuestion,
)
from .services import generate_quiz, summarize_chat

BASE_DIR = Path(__file__).resolve().parents[1]
SUMMARY_DIR = BASE_DIR / "chat" / "summation"
RECORD_DIR = BASE_DIR / "chat" / "record"


def latest_record_file(user_id: str) -> Path | None:
    user_dir = RECORD_DIR / user_id
    if not user_dir.exists():
        return None
    record_files = list(user_dir.glob(f"{user_id}-*.txt"))
    if not record_files:
        return None
    return max(record_files, key=lambda path: path.stat().st_mtime)


def parse_choices(raw_choices: str) -> list[str]:
    try:
        parsed = json.loads(raw_choices)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def stringify_list(values: list[str] | None) -> str | None:
    if values is None:
        return None
    return json.dumps(values, ensure_ascii=False)


def normalize_question_text(text: str) -> str:
    if not text:
        return ""
    stripped = re.sub(r"```json\s*([\s\S]*?)```", r"\1", text, flags=re.IGNORECASE)
    stripped = re.sub(r"```([\s\S]*?)```", r"\1", stripped)
    stripped = stripped.lower()
    stripped = re.sub(r"[^\w\s가-힣]", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def is_similar_question(base_text: str, candidate_text: str) -> bool:
    if not base_text or not candidate_text:
        return False
    if base_text == candidate_text:
        return True
    if base_text in candidate_text or candidate_text in base_text:
        shorter = base_text if len(base_text) <= len(candidate_text) else candidate_text
        if len(shorter) >= 12:
            return True
    similarity = SequenceMatcher(None, base_text, candidate_text).ratio()
    return similarity >= 0.9


def get_existing_question_texts() -> list[str]:
    questions = QuizQuestion.objects.values_list("question", flat=True)
    normalized_questions: list[str] = []
    for question_text in questions:
        normalized = normalize_question_text(question_text or "")
        if normalized:
            normalized_questions.append(normalized)
    return normalized_questions


def quiz_to_response(
    quiz: Quiz,
    current_user: User | None = None,
    scope: str | None = "user",
) -> dict:
    question = quiz.questions.order_by("id").first()
    if not question:
        raise AppError(404, "퀴즈 문항을 찾을 수 없습니다.")

    answer_history: list[str] = []
    has_correct_attempt = False
    has_wrong_attempt = False
    current_index = None
    total_count = None

    if current_user:
        answers = QuizAnswer.objects.filter(
            question=question,
            user=current_user,
        ).order_by("created_at")
        answer_history = [answer.answer_text for answer in answers]
        has_correct_attempt = any(answer.is_correct for answer in answers)
        has_wrong_attempt = any(answer.is_wrong for answer in answers)

        if scope:
            quiz_scope = Quiz.objects.all()
            if scope == "user":
                quiz_scope = quiz_scope.filter(user=current_user)
            total_count = quiz_scope.count()
            if total_count:
                current_index = quiz_scope.filter(id__lte=quiz.id).count()

    return {
        "id": quiz.id,
        "title": quiz.title,
        "link": quiz.link or "",
        "question": question.question,
        "choices": parse_choices(question.choices),
        "correct": question.correct,
        "wrong": parse_choices(question.wrong),
        "explanation": question.explanation,
        "reference": question.reference,
        "created_at": quiz.created_at,
        "has_correct_attempt": has_correct_attempt,
        "has_wrong_attempt": has_wrong_attempt,
        "answer_history": answer_history,
        "tried_at": quiz.tried_at,
        "solved_at": quiz.solved_at,
        "current_index": current_index,
        "total_count": total_count,
    }


def admin_quiz_response(quiz: Quiz, source_user_id: str) -> dict:
    response = quiz_to_response(quiz)
    response["source_user_id"] = source_user_id
    return response


def generate_quiz_for_user(
    target_user: User,
    progress_callback: Callable[[int], None] | None = None,
) -> Quiz:
    record_file = latest_record_file(target_user.user_id)
    if not record_file or not record_file.exists():
        raise AppError(404, "대화 기록이 없습니다.")

    content = record_file.read_text(encoding="utf-8")
    if progress_callback:
        progress_callback(5)

    summary_date = timezone.now()
    summary = summarize_chat(content, summary_date)
    if progress_callback:
        progress_callback(20)

    existing_questions = get_existing_question_texts()
    attempts = 5
    duplicate_attempts = 0
    invalid_attempts = 0
    quiz_payloads: list[dict[str, object]] = []

    for attempt_index in range(attempts):
        candidate_payloads = generate_quiz(summary)
        for candidate_payload in candidate_payloads:
            if len(quiz_payloads) >= 5:
                break
            question_text = str(candidate_payload.get("question", "") or "")
            normalized_question = normalize_question_text(question_text)
            if not normalized_question:
                invalid_attempts += 1
                continue
            if any(is_similar_question(existing, normalized_question) for existing in existing_questions):
                duplicate_attempts += 1
                continue
            quiz_payloads.append(candidate_payload)
            existing_questions.append(normalized_question)
        if len(quiz_payloads) >= 3:
            break
        if progress_callback:
            progress_callback(20 + int(((attempt_index + 1) / attempts) * 40))

    if not quiz_payloads:
        if duplicate_attempts and duplicate_attempts + invalid_attempts == attempts:
            raise AppError(409, "유사한 문제가 이미 있습니다.")
        raise AppError(500, "퀴즈 생성에 실패했습니다.")

    user_summary_dir = SUMMARY_DIR / target_user.user_id
    user_summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = user_summary_dir / f"{target_user.user_id}-{summary_date.strftime('%Y-%m-%d-%H%M')}_sum.txt"
    summary_file.write_text(summary, encoding="utf-8")

    created_quizzes: list[Quiz] = []
    with transaction.atomic():
        ChatSummary.objects.create(
            user=target_user,
            file_path=str(summary_file),
            summary_date=summary_date,
        )

        for quiz_payload in quiz_payloads:
            choices = quiz_payload.get("choices", [])
            if not isinstance(choices, list):
                choices = []

            quiz = Quiz.objects.create(
                user=target_user,
                title="",
                link=str(quiz_payload.get("link", "") or ""),
            )
            question = QuizQuestion.objects.create(
                quiz=quiz,
                question=str(quiz_payload.get("question", "") or ""),
                choices=json.dumps(choices, ensure_ascii=False),
                correct=str(quiz_payload.get("correct", "") or ""),
                wrong=json.dumps(quiz_payload.get("wrong", []), ensure_ascii=False),
                explanation=str(quiz_payload.get("explanation", "") or ""),
                reference=str(quiz_payload.get("reference", "") or ""),
            )
            quiz.title = f"quiz{quiz.id}"
            quiz.save(update_fields=["title"])

            if question.correct:
                QuizCorrect.objects.create(
                    quiz=quiz,
                    question=question,
                    answer_text=question.correct,
                )

            wrong_list = quiz_payload.get("wrong", [])
            if isinstance(wrong_list, list):
                for wrong_answer in wrong_list:
                    if not wrong_answer:
                        continue
                    QuizWrong.objects.create(
                        quiz=quiz,
                        question=question,
                        answer_text=str(wrong_answer),
                    )
            created_quizzes.append(quiz)

    if progress_callback:
        progress_callback(90)

    if not created_quizzes:
        raise AppError(500, "퀴즈 생성에 실패했습니다.")
    return created_quizzes[0]


def shuffle_question_choices(question: QuizQuestion) -> bool:
    choices = parse_choices(question.choices)
    if not choices:
        return False
    random.shuffle(choices)
    question.choices = json.dumps(choices, ensure_ascii=False)
    question.save(update_fields=["choices"])
    return True


def delete_quiz_records(quiz: Quiz) -> None:
    question_ids = list(quiz.questions.values_list("id", flat=True))
    if question_ids:
        WrongQuestion.objects.filter(question_id__in=question_ids).delete()
    quiz.delete()


def run_quiz_job() -> None:
    if not RECORD_DIR.exists():
        return

    for user_dir in RECORD_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        user_id = user_dir.name
        user = User.objects.filter(user_id=user_id).first()
        if not user:
            continue

        record_file = latest_record_file(user_id)
        if not record_file:
            continue

        record_mtime = datetime.utcfromtimestamp(record_file.stat().st_mtime)
        latest_summary = ChatSummary.objects.filter(user=user).order_by("-summary_date").first()
        if latest_summary and latest_summary.summary_date and latest_summary.summary_date.replace(tzinfo=None) >= record_mtime:
            continue

        content = record_file.read_text(encoding="utf-8")
        if not content.strip():
            continue

        summary_date = timezone.now()
        summary = summarize_chat(content, summary_date)
        user_summary_dir = SUMMARY_DIR / user_id
        user_summary_dir.mkdir(parents=True, exist_ok=True)
        summary_file = user_summary_dir / f"{user_id}-{summary_date.strftime('%Y-%m-%d-%H%M')}_sum.txt"
        summary_file.write_text(summary, encoding="utf-8")

        with transaction.atomic():
            ChatSummary.objects.create(user=user, file_path=str(summary_file), summary_date=summary_date)
            quiz_payloads = generate_quiz(summary)
            for quiz_payload in quiz_payloads:
                choices = quiz_payload.get("choices", [])
                if not isinstance(choices, list):
                    choices = []
                quiz = Quiz.objects.create(
                    user=user,
                    title="",
                    link=str(quiz_payload.get("link", "") or ""),
                )
                QuizQuestion.objects.create(
                    quiz=quiz,
                    question=str(quiz_payload.get("question", "") or ""),
                    choices=json.dumps(choices, ensure_ascii=False),
                    correct=str(quiz_payload.get("correct", "") or ""),
                    wrong=json.dumps(quiz_payload.get("wrong", []), ensure_ascii=False),
                    explanation=str(quiz_payload.get("explanation", "") or ""),
                    reference=str(quiz_payload.get("reference", "") or ""),
                )
                quiz.title = f"quiz{quiz.id}"
                quiz.save(update_fields=["title"])
