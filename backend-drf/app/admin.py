import os
from typing import Optional

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from app.models import (
    AdminUser,
    BackgroundJob,
    ChatRecord,
    ChatSummary,
    CoachStudent,
    CoachUser,
    GeneralUser,
    Quiz,
    QuizAnswer,
    QuizCorrect,
    QuizQuestion,
    QuizWrong,
    User,
    WrongQuestion,
)


class ChatSummaryAdminForm(forms.ModelForm):
    user_id = forms.CharField(label="User id", max_length=50, required=False)
    user_name = forms.CharField(label="User name", max_length=100, required=False)
    email = forms.EmailField(label="Email", max_length=255, required=False)
    role = forms.ChoiceField(label="Role", choices=User.ROLE_CHOICES, required=False)
    token = forms.IntegerField(label="Token", min_value=0, required=False)
    is_active = forms.BooleanField(label="Is active", required=False)

    class Meta:
        model = ChatSummary
        fields = ("user", "file_path", "summary_date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(self.instance, "user", None)
        if self.instance.pk and user:
            self.fields["user_id"].initial = user.user_id
            self.fields["user_name"].initial = user.user_name
            self.fields["email"].initial = user.email
            self.fields["role"].initial = user.role
            self.fields["token"].initial = user.token
            self.fields["is_active"].initial = user.is_active
        for field_name in ("user_id", "user_name", "email"):
            if field_name in self.fields:
                self.fields[field_name].disabled = True

    def clean(self):
        cleaned = super().clean()
        user = getattr(self.instance, "user", None)
        if user:
            user_id = cleaned.get("user_id")
            if user_id and User.objects.exclude(pk=user.pk).filter(user_id=user_id).exists():
                self.add_error("user_id", "이미 사용 중인 User id입니다.")
            email = cleaned.get("email")
            if email and User.objects.exclude(pk=user.pk).filter(email=email).exists():
                self.add_error("email", "이미 사용 중인 Email입니다.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        user = getattr(instance, "user", None)
        if user:
            user.role = self.cleaned_data.get("role", user.role)
            user.token = self.cleaned_data.get("token", user.token)
            user.is_active = self.cleaned_data.get("is_active", user.is_active)
            if commit:
                user.save()
        if commit:
            self.save_m2m()
        return instance


class QuizAdminForm(forms.ModelForm):
    user_id = forms.CharField(label="User id", max_length=50, required=False)
    user_name = forms.CharField(label="User name", max_length=100, required=False)
    email = forms.EmailField(label="Email", max_length=255, required=False)
    role = forms.ChoiceField(label="Role", choices=User.ROLE_CHOICES, required=False)
    token = forms.IntegerField(label="Token", min_value=0, required=False)
    is_active = forms.BooleanField(label="Is active", required=False)

    class Meta:
        model = Quiz
        fields = ("user", "title", "link", "tried_at", "solved_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(self.instance, "user", None)
        if self.instance.pk and user:
            self.fields["user_id"].initial = user.user_id
            self.fields["user_name"].initial = user.user_name
            self.fields["email"].initial = user.email
            self.fields["role"].initial = user.role
            self.fields["token"].initial = user.token
            self.fields["is_active"].initial = user.is_active
        for field_name in ("user_id", "user_name", "email"):
            if field_name in self.fields:
                self.fields[field_name].disabled = True

    def clean(self):
        cleaned = super().clean()
        user = getattr(self.instance, "user", None)
        if user:
            user_id = cleaned.get("user_id")
            if user_id and User.objects.exclude(pk=user.pk).filter(user_id=user_id).exists():
                self.add_error("user_id", "이미 사용 중인 User id입니다.")
            email = cleaned.get("email")
            if email and User.objects.exclude(pk=user.pk).filter(email=email).exists():
                self.add_error("email", "이미 사용 중인 Email입니다.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        user = getattr(instance, "user", None)
        if user:
            user.role = self.cleaned_data.get("role", user.role)
            user.token = self.cleaned_data.get("token", user.token)
            user.is_active = self.cleaned_data.get("is_active", user.is_active)
            if commit:
                user.save()
        if commit:
            self.save_m2m()
        return instance


def render_user_link(user: Optional[User]) -> str:
    if not user:
        return "-"
    url = reverse("admin:app_user_change", args=[user.pk])
    return format_html('<a href="{}">{}</a>', url, user.user_id)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "user_name", "email", "role", "token", "is_active", "created_at", "last_logined")
    list_filter = ("role", "is_active", "created_at")
    search_fields = ("user_id", "user_name", "email")
    readonly_fields = ("created_at", "last_logined", "deactivated_at")
    ordering = ("-created_at",)
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("user_id", "user_name", "email", "password_hash")
        }),
        ("User Settings", {
            "fields": ("role", "token", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "last_logined", "deactivated_at")
        }),
    )


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ("get_user_id", "get_user_name", "get_email", "get_role", "get_token", "get_is_active", "created_at")
    list_display_links = ()
    search_fields = ("user__user_id", "user__user_name", "user__email")
    list_filter = ("user__is_active", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("Admin User Info", {
            "fields": ("user", "created_at")
        }),
    )
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="Email", ordering="user__email")
    def get_email(self, obj):
        return obj.user.email
    
    @admin.display(description="Role")
    def get_role(self, obj):
        return obj.user.role
    
    @admin.display(description="Token")
    def get_token(self, obj):
        return obj.user.token
    
    @admin.display(description="Active", boolean=True)
    def get_is_active(self, obj):
        return obj.user.is_active


@admin.register(CoachUser)
class CoachUserAdmin(admin.ModelAdmin):
    list_display = ("get_user_id", "get_user_name", "get_email", "get_token", "get_is_active", "created_at")
    list_display_links = ()
    search_fields = ("user__user_id", "user__user_name", "user__email")
    list_filter = ("user__is_active", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("Coach User Info", {
            "fields": ("user", "created_at")
        }),
    )
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="Email", ordering="user__email")
    def get_email(self, obj):
        return obj.user.email
    
    @admin.display(description="Token")
    def get_token(self, obj):
        return obj.user.token
    
    @admin.display(description="Active", boolean=True)
    def get_is_active(self, obj):
        return obj.user.is_active


@admin.register(GeneralUser)
class GeneralUserAdmin(admin.ModelAdmin):
    list_display = ("get_user_id", "get_user_name", "get_email", "get_token", "get_is_active", "created_at")
    list_display_links = ()
    search_fields = ("user__user_id", "user__user_name", "user__email")
    list_filter = ("user__is_active", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("General User Info", {
            "fields": ("user", "created_at")
        }),
    )
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="Email", ordering="user__email")
    def get_email(self, obj):
        return obj.user.email
    
    @admin.display(description="Token")
    def get_token(self, obj):
        return obj.user.token
    
    @admin.display(description="Active", boolean=True)
    def get_is_active(self, obj):
        return obj.user.is_active


@admin.register(CoachStudent)
class CoachStudentAdmin(admin.ModelAdmin):
    list_display = ("get_coach_id", "get_coach_name", "get_student_id", "get_student_name", "created_at")
    list_display_links = ()
    search_fields = ("coach__user__user_id", "coach__user__user_name", "student__user__user_id", "student__user__user_name")
    readonly_fields = ("created_at",)
    raw_id_fields = ("coach", "student")
    
    @admin.display(description="Coach ID", ordering="coach__user__user_id")
    def get_coach_id(self, obj):
        return render_user_link(obj.coach.user)
    
    @admin.display(description="Coach Name", ordering="coach__user__user_name")
    def get_coach_name(self, obj):
        return obj.coach.user.user_name
    
    @admin.display(description="Student ID", ordering="student__user__user_id")
    def get_student_id(self, obj):
        return render_user_link(obj.student.user)
    
    @admin.display(description="Student Name", ordering="student__user__user_name")
    def get_student_name(self, obj):
        return obj.student.user.user_name


@admin.register(ChatRecord)
class ChatRecordAdmin(admin.ModelAdmin):
    form = ChatSummaryAdminForm
    list_display = ("id", "get_user_id", "get_user_name", "get_file_name", "created_at")
    list_filter = ("created_at", "user__user_id")
    search_fields = ("user__user_id", "user__user_name", "file_path")
    readonly_fields = ("created_at", "get_file_content", "user_created_at", "user_last_logined", "user_deactivated_at")
    
    def get_fieldsets(self, request, obj=None):
        base = [
            (
                "User Basic Information",
                {"fields": ("user_id", "user_name", "email")},
            ),
            (
                "User Settings",
                {"fields": ("role", "token", "is_active")},
            ),
            (
                "User Timestamps",
                {"fields": ("user_created_at", "user_last_logined", "user_deactivated_at")},
            ),
            (
                "File Content",
                {"fields": ("get_file_content",), "classes": ("collapse",)},
            ),
        ]
        if obj is None:
            return [
                ("Chat Record Info", {"fields": ("user", "file_path", "created_at")}),
                *base,
            ]
        return [
            ("Chat Record Info", {"fields": ("file_path", "created_at")}),
            *base,
        ]
    
    @admin.display(description="Record ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="User Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="File Name")
    def get_file_name(self, obj):
        return os.path.basename(obj.file_path)
    
    @admin.display(description="Created at")
    def user_created_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.created_at

    @admin.display(description="Last logined")
    def user_last_logined(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.last_logined or "-"

    @admin.display(description="Deactivated at")
    def user_deactivated_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.deactivated_at or "-"
    
    @admin.display(description="File Content")
    def get_file_content(self, obj):
        try:
            if os.path.exists(obj.file_path):
                with open(obj.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) > 5000:
                    content = content[:5000] + "\n\n... (truncated)"
                return format_html(
                    "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                    "<div style='background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: monospace; max-height: 500px; overflow-y: auto;'>{}</div>",
                    obj.file_path,
                    content
                )
            else:
                return format_html(
                    "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                    "<div style='color: red;'>File not found at: {}</div>",
                    obj.file_path,
                    obj.file_path
                )
        except Exception as e:
            return format_html(
                "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                "<div style='color: red;'>Error reading file: {}</div>",
                obj.file_path,
                str(e)
            )


@admin.register(ChatSummary)
class ChatSummaryAdmin(admin.ModelAdmin):
    form = ChatSummaryAdminForm
    list_display = ("id", "get_user_id", "get_user_name", "get_file_name", "summary_date")
    list_filter = ("summary_date", "user__user_id")
    search_fields = ("user__user_id", "user__user_name", "file_path")
    readonly_fields = ("summary_date", "get_file_content", "user_created_at", "user_last_logined", "user_deactivated_at")

    def get_fieldsets(self, request, obj=None):
        base = [
            (
                "User Basic Information",
                {"fields": ("user_id", "user_name", "email")},
            ),
            (
                "User Settings",
                {"fields": ("role", "token", "is_active")},
            ),
            (
                "User Timestamps",
                {"fields": ("user_created_at", "user_last_logined", "user_deactivated_at")},
            ),
            (
                "File Content",
                {"fields": ("get_file_content",), "classes": ("collapse",)},
            ),
        ]
        if obj is None:
            return [
                ("Chat Summary Info", {"fields": ("user", "file_path", "summary_date")}),
                *base,
            ]
        return [
            ("Chat Summary Info", {"fields": ("file_path", "summary_date")}),
            *base,
        ]
    
    @admin.display(description="Summary ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="User Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="File Name")
    def get_file_name(self, obj):
        return os.path.basename(obj.file_path)
    
    @admin.display(description="Created at")
    def user_created_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.created_at

    @admin.display(description="Last logined")
    def user_last_logined(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.last_logined or "-"

    @admin.display(description="Deactivated at")
    def user_deactivated_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.deactivated_at or "-"
    
    @admin.display(description="File Content")
    def get_file_content(self, obj):
        try:
            if os.path.exists(obj.file_path):
                with open(obj.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content) > 5000:
                    content = content[:5000] + "\n\n... (truncated)"
                return format_html(
                    "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                    "<div style='background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: monospace; max-height: 500px; overflow-y: auto;'>{}</div>",
                    obj.file_path,
                    content
                )
            else:
                return format_html(
                    "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                    "<div style='color: red;'>File not found</div>",
                    obj.file_path
                )
        except Exception as e:
            return format_html(
                "<div style='margin-bottom: 10px;'><strong>File Path:</strong> {}</div>"
                "<div style='color: red;'>Error reading file: {}</div>",
                obj.file_path,
                str(e)
            )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm
    list_display = ("id", "title", "get_user_id", "get_user_name", "created_at", "tried_at", "solved_at")
    list_filter = ("created_at", "tried_at", "solved_at", "user__user_id")
    search_fields = ("title", "user__user_id", "user__user_name")
    readonly_fields = ("created_at", "get_quiz_details", "user_created_at", "user_last_logined", "user_deactivated_at")
    raw_id_fields = ("user",)

    def get_fieldsets(self, request, obj=None):
        base = [
            (
                "User Basic Information",
                {"fields": ("user_id", "user_name", "email")},
            ),
            (
                "User Settings",
                {"fields": ("role", "token", "is_active")},
            ),
            (
                "User Timestamps",
                {"fields": ("user_created_at", "user_last_logined", "user_deactivated_at")},
            ),
            (
                "Quiz Details",
                {"fields": ("get_quiz_details",), "classes": ("collapse",)},
            ),
        ]
        if obj is None:
            return [
                ("Quiz Info", {"fields": ("user", "title", "link", "tried_at", "solved_at")}),
                *base,
            ]
        return [
            ("Quiz Info", {"fields": ("title", "link", "created_at", "tried_at", "solved_at")}),
            *base,
        ]
    
    @admin.display(description="Quiz ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="User Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="Quiz Details")
    def get_quiz_details(self, obj):
        return format_html(
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Title:</strong> {}<br>"
            "<strong>User ID:</strong> {}<br>"
            "<strong>User Name:</strong> {}<br>"
            "<strong>User Email:</strong> {}<br>"
            "<strong>Link:</strong> <a href='{}' target='_blank'>{}</a><br>"
            "<strong>Created At:</strong> {}<br>"
            "<strong>Tried At:</strong> {}<br>"
            "<strong>Solved At:</strong> {}<br>",
            obj.id,
            obj.title,
            obj.user.user_id,
            obj.user.user_name,
            obj.user.email,
            obj.link if obj.link else "#",
            obj.link if obj.link else "N/A",
            obj.created_at,
            obj.tried_at or "Not yet",
            obj.solved_at or "Not yet"
        )

    @admin.display(description="Created at")
    def user_created_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.created_at

    @admin.display(description="Last logined")
    def user_last_logined(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.last_logined or "-"

    @admin.display(description="Deactivated at")
    def user_deactivated_at(self, obj):
        if not obj or not obj.user:
            return "-"
        return obj.user.deactivated_at or "-"


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "get_quiz_title", "get_quiz_user_id", "get_question_short", "created_at")
    list_filter = ("created_at", "quiz__user__user_id")
    search_fields = ("question", "quiz__title", "quiz__user__user_id")
    readonly_fields = ("created_at", "get_question_details")
    raw_id_fields = ("quiz",)
    
    fieldsets = (
        ("Question Info", {
            "fields": ("quiz", "question", "choices", "correct", "wrong", "explanation", "reference", "created_at")
        }),
        ("Question Details", {
            "fields": ("get_question_details",),
            "classes": ("collapse",)
        }),
    )
    
    @admin.display(description="Question ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="Quiz Title", ordering="quiz__title")
    def get_quiz_title(self, obj):
        return obj.quiz.title
    
    @admin.display(description="Quiz User ID", ordering="quiz__user__user_id")
    def get_quiz_user_id(self, obj):
        return render_user_link(obj.quiz.user)
    
    @admin.display(description="Question")
    def get_question_short(self, obj):
        text = obj.question
        return text[:50] + "..." if len(text) > 50 else text
    
    @admin.display(description="Question Details")
    def get_question_details(self, obj):
        return format_html(
            "<strong>Question ID:</strong> {}<br>"
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Quiz Title:</strong> {}<br>"
            "<strong>Quiz User ID:</strong> {}<br>"
            "<strong>Quiz User Name:</strong> {}<br>"
            "<hr>"
            "<strong>Question:</strong><br>{}<br><br>"
            "<strong>Correct Answer:</strong><br>{}<br><br>"
            "<strong>Wrong Answer:</strong><br>{}<br><br>"
            "<strong>Explanation:</strong><br>{}<br><br>"
            "<strong>Reference:</strong><br>{}<br>",
            obj.id,
            obj.quiz.id,
            obj.quiz.title,
            obj.quiz.user.user_id,
            obj.quiz.user.user_name,
            obj.question,
            obj.correct,
            obj.wrong,
            obj.explanation,
            obj.reference
        )


@admin.register(QuizCorrect)
class QuizCorrectAdmin(admin.ModelAdmin):
    list_display = ("id", "get_quiz_id", "get_quiz_user_id", "get_question_short", "answer_text", "created_at")
    list_filter = ("created_at", "quiz__user__user_id")
    search_fields = ("answer_text", "quiz__title", "question__question")
    readonly_fields = ("created_at", "get_correct_details")
    raw_id_fields = ("quiz", "question")
    
    fieldsets = (
        ("Correct Answer Info", {
            "fields": ("quiz", "question", "answer_text", "created_at")
        }),
        ("Details", {
            "fields": ("get_correct_details",),
            "classes": ("collapse",)
        }),
    )
    
    @admin.display(description="Correct ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="Quiz ID", ordering="quiz__id")
    def get_quiz_id(self, obj):
        return obj.quiz.id
    
    @admin.display(description="Quiz User ID", ordering="quiz__user__user_id")
    def get_quiz_user_id(self, obj):
        return render_user_link(obj.quiz.user)
    
    @admin.display(description="Question")
    def get_question_short(self, obj):
        text = obj.question.question
        return text[:30] + "..." if len(text) > 30 else text
    
    @admin.display(description="Correct Answer Details")
    def get_correct_details(self, obj):
        return format_html(
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Quiz Title:</strong> {}<br>"
            "<strong>Quiz User ID:</strong> {}<br>"
            "<strong>Question ID:</strong> {}<br>"
            "<strong>Question:</strong><br>{}<br><br>"
            "<strong>Correct Answer:</strong><br>{}<br>",
            obj.quiz.id,
            obj.quiz.title,
            obj.quiz.user.user_id,
            obj.question.id,
            obj.question.question,
            obj.answer_text
        )


@admin.register(QuizWrong)
class QuizWrongAdmin(admin.ModelAdmin):
    list_display = ("id", "get_quiz_id", "get_quiz_user_id", "get_question_short", "answer_text", "created_at")
    list_filter = ("created_at", "quiz__user__user_id")
    search_fields = ("answer_text", "quiz__title", "question__question")
    readonly_fields = ("created_at", "get_wrong_details")
    raw_id_fields = ("quiz", "question")
    
    fieldsets = (
        ("Wrong Answer Info", {
            "fields": ("quiz", "question", "answer_text", "created_at")
        }),
        ("Details", {
            "fields": ("get_wrong_details",),
            "classes": ("collapse",)
        }),
    )
    
    @admin.display(description="Wrong ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="Quiz ID", ordering="quiz__id")
    def get_quiz_id(self, obj):
        return obj.quiz.id
    
    @admin.display(description="Quiz User ID", ordering="quiz__user__user_id")
    def get_quiz_user_id(self, obj):
        return obj.quiz.user.user_id
    
    @admin.display(description="Question")
    def get_question_short(self, obj):
        text = obj.question.question
        return text[:30] + "..." if len(text) > 30 else text
    
    @admin.display(description="Wrong Answer Details")
    def get_wrong_details(self, obj):
        return format_html(
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Quiz Title:</strong> {}<br>"
            "<strong>Quiz User ID:</strong> {}<br>"
            "<strong>Question ID:</strong> {}<br>"
            "<strong>Question:</strong><br>{}<br><br>"
            "<strong>Wrong Answer:</strong><br>{}<br>",
            obj.quiz.id,
            obj.quiz.title,
            obj.quiz.user.user_id,
            obj.question.id,
            obj.question.question,
            obj.answer_text
        )


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "get_question_text", "get_user_id", "get_user_name", "is_correct", "is_wrong", "created_at")
    list_filter = ("is_correct", "is_wrong", "created_at", "user__user_id")
    search_fields = ("answer_text", "user__user_id", "user__user_name", "question__question")
    readonly_fields = ("created_at", "get_answer_details")
    raw_id_fields = ("question", "user")
    
    fieldsets = (
        ("Answer Info", {
            "fields": ("question", "user", "answer_text", "is_correct", "is_wrong", "created_at")
        }),
        ("Details", {
            "fields": ("get_answer_details",),
            "classes": ("collapse",)
        }),
    )
    
    @admin.display(description="Answer ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="Question", ordering="question__question")
    def get_question_text(self, obj):
        text = obj.question.question
        return text[:50] + "..." if len(text) > 50 else text
    
    @admin.display(description="User ID", ordering="user__user_id")
    def get_user_id(self, obj):
        return render_user_link(obj.user)
    
    @admin.display(description="User Name", ordering="user__user_name")
    def get_user_name(self, obj):
        return obj.user.user_name
    
    @admin.display(description="Answer Details")
    def get_answer_details(self, obj):
        return format_html(
            "<strong>Answer ID:</strong> {}<br>"
            "<strong>User ID:</strong> {}<br>"
            "<strong>User Name:</strong> {}<br>"
            "<strong>User Email:</strong> {}<br>"
            "<hr>"
            "<strong>Question ID:</strong> {}<br>"
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Quiz Title:</strong> {}<br>"
            "<strong>Question:</strong><br>{}<br><br>"
            "<strong>User's Answer:</strong><br>{}<br><br>"
            "<strong>Is Correct:</strong> {}<br>"
            "<strong>Is Wrong:</strong> {}<br>",
            obj.id,
            obj.user.user_id,
            obj.user.user_name,
            obj.user.email,
            obj.question.id,
            obj.question.quiz.id,
            obj.question.quiz.title,
            obj.question.question,
            obj.answer_text,
            "✓ Yes" if obj.is_correct else "✗ No",
            "✓ Yes" if obj.is_wrong else "✗ No"
        )


@admin.register(WrongQuestion)
class WrongQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "get_question_text", "get_creator_id", "get_solver_id", "last_solved_at")
    list_filter = ("last_solved_at", "question_creator__user_id", "solver_user__user_id")
    search_fields = ("question_creator__user_id", "solver_user__user_id", "correct_answer", "wrong_answer", "question__question")
    readonly_fields = ("get_wrong_question_details",)
    raw_id_fields = ("question", "question_creator", "solver_user")
    
    fieldsets = (
        ("Wrong Question Info", {
            "fields": ("question", "question_creator", "solver_user", "correct_answer", "wrong_answer", "reference_link", "user_answers", "last_solved_at")
        }),
        ("Details", {
            "fields": ("get_wrong_question_details",),
            "classes": ("collapse",)
        }),
    )
    
    @admin.display(description="Wrong Q ID", ordering="id")
    def id(self, obj):
        return obj.id
    
    @admin.display(description="Question", ordering="question__question")
    def get_question_text(self, obj):
        text = obj.question.question
        return text[:50] + "..." if len(text) > 50 else text
    
    @admin.display(description="Creator ID", ordering="question_creator__user_id")
    def get_creator_id(self, obj):
        return render_user_link(obj.question_creator)
    
    @admin.display(description="Solver ID", ordering="solver_user__user_id")
    def get_solver_id(self, obj):
        return render_user_link(obj.solver_user)
    
    @admin.display(description="Wrong Question Details")
    def get_wrong_question_details(self, obj):
        return format_html(
            "<strong>Wrong Question ID:</strong> {}<br>"
            "<strong>Question ID:</strong> {}<br>"
            "<strong>Quiz ID:</strong> {}<br>"
            "<strong>Quiz Title:</strong> {}<br>"
            "<hr>"
            "<strong>Creator User ID:</strong> {}<br>"
            "<strong>Creator User Name:</strong> {}<br>"
            "<strong>Solver User ID:</strong> {}<br>"
            "<strong>Solver User Name:</strong> {}<br>"
            "<hr>"
            "<strong>Question:</strong><br>{}<br><br>"
            "<strong>Correct Answer:</strong><br>{}<br><br>"
            "<strong>Wrong Answer:</strong><br>{}<br><br>"
            "<strong>User's Answers:</strong><br>{}<br><br>"
            "<strong>Reference Link:</strong> <a href='{}' target='_blank'>{}</a><br>"
            "<strong>Last Solved At:</strong> {}<br>",
            obj.id,
            obj.question.id,
            obj.question.quiz.id,
            obj.question.quiz.title,
            obj.question_creator.user_id,
            obj.question_creator.user_name,
            obj.solver_user.user_id,
            obj.solver_user.user_name,
            obj.question.question,
            obj.correct_answer,
            obj.wrong_answer,
            obj.user_answers,
            obj.reference_link if obj.reference_link else "#",
            obj.reference_link if obj.reference_link else "N/A",
            obj.last_solved_at or "Not yet"
        )


@admin.register(BackgroundJob)
class BackgroundJobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "job_type", "status", "progress", "created_at", "updated_at")
    list_filter = ("job_type", "status", "created_at")
    search_fields = ("job_id", "message", "error")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    
    fieldsets = (
        ("Job Info", {
            "fields": ("job_id", "job_type", "status", "progress")
        }),
        ("Details", {
            "fields": ("message", "result", "error")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )
