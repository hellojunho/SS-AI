from django.db import models
from django.utils import timezone


class User(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_COACH = "coach"
    ROLE_GENERAL = "general"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "admin"),
        (ROLE_COACH, "coach"),
        (ROLE_GENERAL, "general"),
    ]

    user_id = models.CharField(max_length=50, unique=True)
    user_name = models.CharField(max_length=100)
    password_hash = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_GENERAL)
    created_at = models.DateTimeField(default=timezone.now)
    last_logined = models.DateTimeField(null=True, blank=True)
    token = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def is_authenticated(self) -> bool:
        return True


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id", related_name="admin_profile")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "admin_users"
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"


class CoachUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id", related_name="coach_profile")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "coach_users"
        verbose_name = "Coach User"
        verbose_name_plural = "Coach Users"


class GeneralUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id", related_name="general_profile")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "general_users"
        verbose_name = "General User"
        verbose_name_plural = "General Users"


class CoachStudent(models.Model):
    coach = models.ForeignKey(CoachUser, on_delete=models.CASCADE, db_column="coach_id", related_name="students")
    student = models.ForeignKey(GeneralUser, on_delete=models.CASCADE, db_column="student_id", related_name="coaches")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "coach_students"
        verbose_name = "Coach-Student Relation"
        verbose_name_plural = "Coach-Student Relations"
        constraints = [
            models.UniqueConstraint(fields=["coach", "student"], name="uniq_coach_student"),
        ]


class ChatRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="chat_records")
    file_path = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "chat_records"
        verbose_name = "Chat Record"
        verbose_name_plural = "Chat Records"


class ChatSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="chat_summaries")
    file_path = models.TextField()
    summary_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "chat_summaries"
        verbose_name = "Chat Summary"
        verbose_name_plural = "Chat Summaries"


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="quizzes")
    title = models.CharField(max_length=100)
    link = models.TextField(default="")
    created_at = models.DateTimeField(default=timezone.now)
    tried_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "quizzes"
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column="quiz_id", related_name="questions")
    question = models.TextField()
    choices = models.TextField(default="[]")
    correct = models.TextField()
    wrong = models.TextField()
    explanation = models.TextField()
    reference = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "quiz_questions"
        verbose_name = "Quiz Question"
        verbose_name_plural = "Quiz Questions"


class QuizCorrect(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column="quiz_id")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, db_column="quiz_question_id", related_name="correct_entries")
    answer_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "quiz_corrects"
        verbose_name = "Quiz Correct Answer"
        verbose_name_plural = "Quiz Correct Answers"


class QuizWrong(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column="quiz_id")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, db_column="quiz_question_id", related_name="wrong_entries")
    answer_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "quiz_wrongs"
        verbose_name = "Quiz Wrong Answer"
        verbose_name_plural = "Quiz Wrong Answers"


class QuizAnswer(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, db_column="quiz_question_id", related_name="answers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="quiz_answers")
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    is_wrong = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "quiz_answers"
        verbose_name = "Quiz Answer"
        verbose_name_plural = "Quiz Answers"


class WrongQuestion(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, db_column="quiz_question_id", related_name="wrong_questions")
    question_creator = models.ForeignKey(User, on_delete=models.CASCADE, db_column="question_creator_id", related_name="created_wrong_questions")
    solver_user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="solver_user_id", related_name="solved_wrong_questions")
    correct_answer = models.TextField()
    wrong_answer = models.TextField()
    reference_link = models.TextField()
    user_answers = models.TextField()
    last_solved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wrong_questions"
        verbose_name = "Wrong Question"
        verbose_name_plural = "Wrong Questions"


class BackgroundJob(models.Model):
    JOB_TYPE_QUIZ_GENERATE = "quiz_generate"
    JOB_TYPE_QUIZ_GENERATE_ALL = "quiz_generate_all"
    JOB_TYPE_DOCS_LEARN = "docs_learn"

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    job_id = models.CharField(max_length=64, unique=True)
    job_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default=STATUS_PENDING)
    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True, default="")
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "background_jobs"
        verbose_name = "Background Job"
        verbose_name_plural = "Background Jobs"
        indexes = [models.Index(fields=["job_type", "created_at"]) ]
