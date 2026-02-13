from datetime import datetime

from rest_framework import serializers

from .models import User

MAX_PASSWORD_BYTES = 1024


def validate_password_length(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise serializers.ValidationError("Password must be 1024 bytes or fewer.")
    return password


class UserCreateSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=50)
    user_name = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=2048, write_only=True)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["admin", "coach", "general"], default="general")

    def validate_password(self, value: str) -> str:
        return validate_password_length(value)

    def validate_role(self, value: str) -> str:
        if value == "admin":
            raise serializers.ValidationError("관리자는 회원가입으로 생성할 수 없습니다.")
        return value


class UserLoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=2048)

    def validate_password(self, value: str) -> str:
        return validate_password_length(value)


class UserOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "user_id",
            "user_name",
            "email",
            "role",
            "created_at",
            "last_logined",
            "is_active",
            "deactivated_at",
        ]


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default="bearer")


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChatResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    reference = serializers.CharField()
    file_path = serializers.CharField()


class ChatHistoryEntrySerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()


class ChatHistoryResponseSerializer(serializers.Serializer):
    date = serializers.CharField()
    entries = ChatHistoryEntrySerializer(many=True)
    is_today = serializers.BooleanField()


class ChatHistoryDatesResponseSerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.CharField())
    today = serializers.CharField()


class SummaryResponseSerializer(serializers.Serializer):
    file_path = serializers.CharField()
    summary = serializers.CharField()


class QuizResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    link = serializers.CharField()
    question = serializers.CharField()
    choices = serializers.ListField(child=serializers.CharField())
    correct = serializers.CharField()
    wrong = serializers.ListField(child=serializers.CharField())
    explanation = serializers.CharField()
    reference = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)
    has_correct_attempt = serializers.BooleanField(default=False)
    has_wrong_attempt = serializers.BooleanField(default=False)
    answer_history = serializers.ListField(child=serializers.CharField(), default=list)
    tried_at = serializers.DateTimeField(allow_null=True)
    solved_at = serializers.DateTimeField(allow_null=True)
    current_index = serializers.IntegerField(allow_null=True)
    total_count = serializers.IntegerField(allow_null=True)


class QuizAnswerCreateSerializer(serializers.Serializer):
    answer = serializers.CharField()


class QuizAnswerResponseSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    answer = serializers.CharField()
    is_correct = serializers.BooleanField()
    is_wrong = serializers.BooleanField()
    has_correct_attempt = serializers.BooleanField()
    has_wrong_attempt = serializers.BooleanField()
    answer_history = serializers.ListField(child=serializers.CharField())
    tried_at = serializers.DateTimeField(allow_null=True)
    solved_at = serializers.DateTimeField(allow_null=True)


class QuizResultSummarySerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    wrong_count = serializers.IntegerField()
    accuracy_rate = serializers.FloatField()


class WrongNoteQuestionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    question = serializers.CharField()
    choices = serializers.ListField(child=serializers.CharField())
    correct = serializers.CharField()
    wrong = serializers.ListField(child=serializers.CharField())
    explanation = serializers.CharField()
    reference = serializers.CharField()
    link = serializers.CharField()


class AdminQuizGenerateRequestSerializer(serializers.Serializer):
    user_id = serializers.CharField()


class AdminQuizResponseSerializer(QuizResponseSerializer):
    source_user_id = serializers.CharField()


class AdminQuizJobResponseSerializer(serializers.Serializer):
    job_id = serializers.CharField()


class AdminQuizJobStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    progress = serializers.IntegerField()
    result = serializers.JSONField(allow_null=True, required=False)
    error = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class AdminUserUpdateSerializer(serializers.Serializer):
    user_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(choices=["admin", "coach", "general"], required=False)
    password = serializers.CharField(required=False, allow_blank=False)

    def validate_password(self, value: str) -> str:
        return validate_password_length(value)


class AdminUserCreateSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=50)
    user_name = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=2048)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["admin", "coach", "general"], default="general")

    def validate_password(self, value: str) -> str:
        return validate_password_length(value)


class CoachStudentCreateSerializer(serializers.Serializer):
    student_user_id = serializers.CharField(max_length=50)


class AdminQuizUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    link = serializers.CharField(required=False, allow_blank=True)
    question = serializers.CharField(required=False, allow_blank=True)
    choices = serializers.ListField(child=serializers.CharField(), required=False)
    correct = serializers.CharField(required=False, allow_blank=True)
    wrong = serializers.ListField(child=serializers.CharField(), required=False)
    explanation = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)


class AdminTrafficBucketSerializer(serializers.Serializer):
    label = serializers.CharField()
    signups = serializers.IntegerField()
    logins = serializers.IntegerField()
    withdrawals = serializers.IntegerField()


class AdminTrafficStatsSerializer(serializers.Serializer):
    period = serializers.CharField()
    buckets = AdminTrafficBucketSerializer(many=True)


class LlmUsageSerializer(serializers.Serializer):
    provider = serializers.CharField()
    model = serializers.CharField()
    total_tokens = serializers.IntegerField()
    used_tokens = serializers.IntegerField()
    remaining_tokens = serializers.IntegerField()
    prompt_tokens = serializers.IntegerField()
    completion_tokens = serializers.IntegerField()
    last_updated = serializers.DateTimeField(allow_null=True)


class LearnStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    progress = serializers.IntegerField()
    message = serializers.CharField()


class WebDocumentPayloadSerializer(serializers.Serializer):
    url = serializers.URLField()
