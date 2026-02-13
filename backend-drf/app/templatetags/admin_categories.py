from __future__ import annotations

from django import template

register = template.Library()

CATEGORY_ORDER: list[tuple[str, list[str]]] = [
    (
        "User",
        [
            "app.User",
            "app.AdminUser",
            "app.CoachUser",
            "app.GeneralUser",
            "app.CoachStudent",
        ],
    ),
    (
        "Quiz",
        [
            "app.Quiz",
            "app.QuizQuestion",
            "app.QuizCorrect",
            "app.QuizWrong",
            "app.QuizAnswer",
            "app.WrongQuestion",
        ],
    ),
    (
        "Chat",
        [
            "app.ChatRecord",
            "app.ChatSummary",
        ],
    ),
    (
        "Task",
        [
            "app.BackgroundJob",
        ],
    ),
]


@register.simple_tag
def get_admin_categories(app_list: list[dict]) -> list[dict]:
    models: list[dict] = []
    for app in app_list:
        app_label = app.get("app_label")
        for model in app.get("models", []):
            models.append({**model, "app_label": app_label})

    used = set()
    categories: list[dict] = []

    for title, model_names in CATEGORY_ORDER:
        bucket = []
        for model_name in model_names:
            for index, model in enumerate(models):
                if index in used:
                    continue
                app_label = model.get("app_label")
                object_name = model.get("object_name")
                if not app_label or not object_name:
                    continue
                if model_name == f"{app_label}.{object_name}":
                    bucket.append(model)
                    used.add(index)
                    break
        if bucket:
            categories.append({"title": title, "models": bucket})

    leftovers = [model for index, model in enumerate(models) if index not in used]
    if leftovers:
        categories.append({"title": "Other", "models": sorted(leftovers, key=lambda item: item.get("name", ""))})

    return categories
