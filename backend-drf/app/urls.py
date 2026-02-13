from django.urls import path

from . import views_auth, views_chat, views_docs_admin, views_llm_admin, views_quiz

urlpatterns = [
    path("auth/register", views_auth.register),
    path("auth/login", views_auth.login),
    path("auth/refresh", views_auth.refresh_token),
    path("auth/me", views_auth.me),
    path("auth/withdraw", views_auth.withdraw_account),
    path("auth/admin/users", views_auth.admin_list_users),
    path("auth/admin/traffic", views_auth.admin_user_traffic),
    path("auth/admin/users/<int:user_id>", views_auth.admin_user_detail),
    path("auth/coach/students", views_auth.coach_students),
    path("auth/coach/students/search", views_auth.coach_search_students),
    path("auth/coach/students/<str:student_user_id>", views_auth.coach_remove_student),

    path("chat/ask", views_chat.ask_chat),
    path("chat/history", views_chat.get_chat_history_dates),
    path("chat/history/<str:date_str>", views_chat.get_chat_history),
    path("chat/summarize", views_chat.summarize_day),

    path("quiz/generate", views_quiz.generate_quiz_from_summary),
    path("quiz/admin/generate", views_quiz.admin_generate_quiz),
    path("quiz/admin/generate-all", views_quiz.admin_generate_all),
    path("quiz/admin/generate/status/<str:job_id>", views_quiz.admin_generate_status),
    path("quiz/admin/list", views_quiz.admin_list_quizzes),
    path("quiz/admin/<int:quiz_id>", views_quiz.admin_quiz_detail),
    path("quiz/admin/<int:quiz_id>/mix", views_quiz.admin_mix_quiz_choices),
    path("quiz/admin/mix-all", views_quiz.admin_mix_all_quiz_choices),
    path("quiz/admin/dedupe", views_quiz.admin_dedupe_quizzes),
    path("quiz/latest", views_quiz.latest_quiz),
    path("quiz/all/first", views_quiz.first_quiz_all),
    path("quiz/all/latest", views_quiz.latest_quiz_all),
    path("quiz/next", views_quiz.next_quiz),
    path("quiz/all/next", views_quiz.next_quiz_all),
    path("quiz/prev", views_quiz.prev_quiz),
    path("quiz/all/prev", views_quiz.prev_quiz_all),
    path("quiz/summary", views_quiz.quiz_summary),
    path("quiz/wrong-notes", views_quiz.wrong_notes),
    path("quiz/<int:quiz_id>", views_quiz.get_quiz),
    path("quiz/<int:quiz_id>/answer", views_quiz.submit_quiz_answer),

    path("admin/docs/upload", views_docs_admin.upload_document),
    path("admin/docs/web", views_docs_admin.upload_web_document),
    path("admin/docs/learn", views_docs_admin.start_learning),
    path("admin/docs/learn/status", views_docs_admin.get_learning_status),

    path("admin/llm/usage", views_llm_admin.get_llm_usage),
]
