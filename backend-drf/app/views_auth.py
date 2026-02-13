from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from .models import (
    ChatRecord,
    ChatSummary,
    CoachStudent,
    CoachUser,
    GeneralUser,
    Quiz,
    QuizAnswer,
    User,
    WrongQuestion,
)
from .permissions import IsAdminRole, IsAuthenticatedJWT, IsCoachRole
from .quiz_logic import delete_quiz_records
from .role_utils import delete_role_profiles, ensure_role_profile, sync_user_role
from .serializers import (
    AdminTrafficStatsSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    CoachStudentCreateSerializer,
    RefreshTokenRequestSerializer,
    TokenSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserOutSerializer,
)


def _token_response(user: User) -> dict:
    access_token = create_access_token(subject=str(user.id), token_version=user.token)
    refresh_token = create_refresh_token(subject=str(user.id), token_version=user.token)
    return TokenSerializer(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    ).data


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request):
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    if User.objects.filter(user_id=payload["user_id"]).exists():
        return Response({"detail": "이미 존재하는 사용자입니다."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=payload["email"]).exists():
        return Response({"detail": "이미 존재하는 이메일입니다."}, status=status.HTTP_400_BAD_REQUEST)

    role_value = str(payload["role"])
    if role_value == User.ROLE_ADMIN:
        return Response({"detail": "관리자는 회원가입으로 생성할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        new_user = User.objects.create(
            user_id=payload["user_id"],
            user_name=payload["user_name"],
            password_hash=hash_password(payload["password"]),
            email=payload["email"],
            role=role_value,
        )
        ensure_role_profile(new_user, role_value)

    return Response(UserOutSerializer(new_user).data)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    user = User.objects.filter(user_id=payload["user_id"]).first()
    if not user or not verify_password(payload["password"], user.password_hash):
        return Response({"detail": "로그인 실패"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"detail": "탈퇴한 계정입니다."}, status=status.HTTP_403_FORBIDDEN)

    user.last_logined = timezone.now()
    user.save(update_fields=["last_logined"])
    return Response(_token_response(user))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = RefreshTokenRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        refresh_payload = decode_refresh_token(serializer.validated_data["refresh_token"])
    except ValueError:
        return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = refresh_payload.get("sub")
    token_version = refresh_payload.get("ver")
    if user_id is None:
        return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

    user = User.objects.filter(id=int(user_id)).first()
    if not user or user.token != token_version:
        return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"detail": "탈퇴한 계정입니다."}, status=status.HTTP_403_FORBIDDEN)

    return Response(_token_response(user))


@api_view(["GET"])
@permission_classes([IsAuthenticatedJWT])
def me(request):
    return Response(UserOutSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticatedJWT])
def withdraw_account(request):
    user = request.user
    user.is_active = False
    user.deactivated_at = timezone.now()
    user.token += 1
    user.save(update_fields=["is_active", "deactivated_at", "token"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_user_traffic(request):
    def add_months(base_dt, months: int):
        total_month = base_dt.month - 1 + months
        year = base_dt.year + total_month // 12
        month = total_month % 12 + 1
        return base_dt.replace(year=year, month=month, day=1)

    def to_utc(target):
        return target.astimezone(ZoneInfo("UTC"))

    def count_between(field_name: str, start, end) -> int:
        start_utc = to_utc(start)
        end_utc = to_utc(end)
        return User.objects.filter(
            **{
                f"{field_name}__isnull": False,
                f"{field_name}__gte": start_utc,
                f"{field_name}__lt": end_utc,
            }
        ).count()

    kst = ZoneInfo("Asia/Seoul")
    now = timezone.now().astimezone(kst)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)
    start_of_year = start_of_day.replace(month=1, day=1)

    periods = [
        ("day", start_of_day),
        ("week", start_of_week),
        ("month", start_of_month),
        ("year", start_of_year),
    ]

    results = []
    for label, start in periods:
        buckets = []
        if label == "day":
            base = start - timedelta(days=11)
            for offset in range(12):
                bucket_start = base + timedelta(days=offset)
                bucket_end = bucket_start + timedelta(days=1)
                buckets.append(
                    {
                        "label": bucket_start.strftime("%m/%d"),
                        "signups": count_between("created_at", bucket_start, bucket_end),
                        "logins": count_between("last_logined", bucket_start, bucket_end),
                        "withdrawals": count_between("deactivated_at", bucket_start, bucket_end),
                    }
                )
        elif label == "week":
            base = start - timedelta(weeks=11)
            for offset in range(12):
                bucket_start = base + timedelta(weeks=offset)
                bucket_end = bucket_start + timedelta(weeks=1)
                buckets.append(
                    {
                        "label": bucket_start.strftime("%m/%d"),
                        "signups": count_between("created_at", bucket_start, bucket_end),
                        "logins": count_between("last_logined", bucket_start, bucket_end),
                        "withdrawals": count_between("deactivated_at", bucket_start, bucket_end),
                    }
                )
        elif label == "month":
            base = add_months(start, -11)
            for offset in range(12):
                bucket_start = add_months(base, offset)
                bucket_end = add_months(bucket_start, 1)
                buckets.append(
                    {
                        "label": bucket_start.strftime("%y.%m"),
                        "signups": count_between("created_at", bucket_start, bucket_end),
                        "logins": count_between("last_logined", bucket_start, bucket_end),
                        "withdrawals": count_between("deactivated_at", bucket_start, bucket_end),
                    }
                )
        else:
            base_year = start.year - 11
            for offset in range(12):
                bucket_start = start.replace(year=base_year + offset)
                bucket_end = bucket_start.replace(year=bucket_start.year + 1)
                buckets.append(
                    {
                        "label": str(bucket_start.year),
                        "signups": count_between("created_at", bucket_start, bucket_end),
                        "logins": count_between("last_logined", bucket_start, bucket_end),
                        "withdrawals": count_between("deactivated_at", bucket_start, bucket_end),
                    }
                )
        results.append({"period": label, "buckets": buckets})

    return Response(AdminTrafficStatsSerializer(results, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdminRole])
def admin_user_detail(request, user_id: int):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"detail": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(UserOutSerializer(user).data)

    if request.method == "PATCH":
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        with transaction.atomic():
            if "email" in payload and payload["email"] != user.email:
                if User.objects.filter(email=payload["email"]).exclude(id=user_id).exists():
                    return Response({"detail": "이미 존재하는 이메일입니다."}, status=status.HTTP_400_BAD_REQUEST)
                user.email = payload["email"]

            if "user_name" in payload:
                user.user_name = payload["user_name"]

            if "role" in payload:
                sync_user_role(user, payload["role"])

            if payload.get("password"):
                user.password_hash = hash_password(payload["password"])
                user.token += 1

            user.save()

        return Response(UserOutSerializer(user).data)

    with transaction.atomic():
        ChatRecord.objects.filter(user=user).delete()
        ChatSummary.objects.filter(user=user).delete()
        QuizAnswer.objects.filter(user=user).delete()
        WrongQuestion.objects.filter(Q(question_creator=user) | Q(solver_user=user)).delete()

        quizzes = list(Quiz.objects.filter(user=user))
        for quiz in quizzes:
            delete_quiz_records(quiz)

        delete_role_profiles(user)
        user.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@permission_classes([IsCoachRole])
def coach_students(request):
    current_user = request.user
    coach_profile, _ = CoachUser.objects.get_or_create(user=current_user)

    if request.method == "GET":
        students = (
            User.objects.filter(general_profile__coaches__coach=coach_profile)
            .order_by("-created_at")
            .distinct()
        )
        return Response(UserOutSerializer(students, many=True).data)

    serializer = CoachStudentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    student_user_id = serializer.validated_data["student_user_id"]

    student_user = User.objects.filter(user_id=student_user_id).first()
    if not student_user or student_user.role != User.ROLE_GENERAL:
        return Response({"detail": "학생 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    student_profile, _ = GeneralUser.objects.get_or_create(user=student_user)
    exists = CoachStudent.objects.filter(coach=coach_profile, student=student_profile).exists()
    if exists:
        return Response({"detail": "이미 등록된 학생입니다."}, status=status.HTTP_400_BAD_REQUEST)

    CoachStudent.objects.create(coach=coach_profile, student=student_profile)
    return Response(UserOutSerializer(student_user).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsCoachRole])
def coach_search_students(request):
    keyword = (request.query_params.get("keyword") or "").strip()
    if not keyword:
        return Response([])

    students = (
        User.objects.filter(role=User.ROLE_GENERAL)
        .filter(Q(user_id__icontains=keyword) | Q(user_name__icontains=keyword) | Q(email__icontains=keyword))
        .order_by("-created_at")[:50]
    )
    return Response(UserOutSerializer(students, many=True).data)


@api_view(["DELETE"])
@permission_classes([IsCoachRole])
def coach_remove_student(request, student_user_id: str):
    current_user = request.user
    coach_profile, _ = CoachUser.objects.get_or_create(user=current_user)

    student_user = User.objects.filter(user_id=student_user_id).first()
    if not student_user:
        return Response({"detail": "학생 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    student_profile = GeneralUser.objects.filter(user=student_user).first()
    if not student_profile:
        return Response({"detail": "학생 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    deleted, _ = CoachStudent.objects.filter(coach=coach_profile, student=student_profile).delete()
    if not deleted:
        return Response({"detail": "등록된 학생이 아닙니다."}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_204_NO_CONTENT)


# Backward-compatible route handler for POST /auth/admin/users
@api_view(["GET", "POST"])
@permission_classes([IsAdminRole])
def admin_list_users(request):
    if request.method == "POST":
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        if User.objects.filter(user_id=payload["user_id"]).exists():
            return Response({"detail": "이미 존재하는 사용자입니다."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=payload["email"]).exists():
            return Response({"detail": "이미 존재하는 이메일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.create(
                user_id=payload["user_id"],
                user_name=payload["user_name"],
                password_hash=hash_password(payload["password"]),
                email=payload["email"],
                role=payload["role"],
            )
            ensure_role_profile(user, payload["role"])

        return Response(UserOutSerializer(user).data, status=status.HTTP_201_CREATED)
    users = User.objects.order_by("-created_at")
    return Response(UserOutSerializer(users, many=True).data)
