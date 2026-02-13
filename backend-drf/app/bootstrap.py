from django.db import connection
from django.utils import timezone

from .auth_utils import hash_password
from .models import AdminUser, CoachUser, GeneralUser, User
from .role_utils import ensure_role_profile


def _table_names() -> set[str]:
    return set(connection.introspection.table_names())


def _column_names(table_name: str) -> set[str]:
    with connection.cursor() as cursor:
        desc = connection.introspection.get_table_description(cursor, table_name)
    return {col.name for col in desc}


def ensure_legacy_columns() -> None:
    if connection.vendor != "mysql":
        return
    tables = _table_names()
    with connection.cursor() as cursor:
        if "quiz_questions" in tables:
            columns = _column_names("quiz_questions")
            if "choices" not in columns:
                cursor.execute("ALTER TABLE quiz_questions ADD COLUMN choices TEXT")
                cursor.execute("UPDATE quiz_questions SET choices = '[]' WHERE choices IS NULL")
                cursor.execute("ALTER TABLE quiz_questions MODIFY COLUMN choices TEXT NOT NULL")

        if "quizzes" in tables:
            columns = _column_names("quizzes")
            if "link" not in columns:
                cursor.execute("ALTER TABLE quizzes ADD COLUMN link TEXT")
                cursor.execute("UPDATE quizzes SET link = '' WHERE link IS NULL")
                cursor.execute("ALTER TABLE quizzes MODIFY COLUMN link TEXT NOT NULL")
            if "created_at" not in columns:
                cursor.execute("ALTER TABLE quizzes ADD COLUMN created_at DATETIME")
                cursor.execute("UPDATE quizzes SET created_at = NOW() WHERE created_at IS NULL")
                cursor.execute(
                    "ALTER TABLE quizzes MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                )

        if "users" in tables:
            columns = _column_names("users")
            if "role" not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'general'")


def ensure_admin_user() -> None:
    if not User.objects.filter(user_id="admin").exists():
        user = User.objects.create(
            user_id="admin",
            user_name="admin",
            password_hash=hash_password("admin"),
            email="admin@example.com",
            role=User.ROLE_ADMIN,
            created_at=timezone.now(),
            token=0,
        )
        AdminUser.objects.get_or_create(user=user)


def ensure_role_tables() -> None:
    for user in User.objects.all().iterator():
        ensure_role_profile(user, user.role)


def bootstrap_all() -> None:
    ensure_legacy_columns()
    ensure_admin_user()
    ensure_role_tables()
