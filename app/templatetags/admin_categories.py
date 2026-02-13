from __future__ import annotations

from django import template

register = template.Library()

CATEGORY_ORDER: list[tuple[str, list[str]]] = [
    (
        "Users",
        [
            "User",
            "AdminUser",
            "CoachUser",
            "GeneralUser",
            "CoachStudent",
        ],
    ),
    (
        "Chat",
        [
            "ChatRecord",
            "ChatSummary",
        ],
    ),
    (
        "Quiz",
        [
            "Quiz",
            "QuizQuestion",
            "QuizCorrect",
            "QuizWrong",
            "QuizAnswer",
            "WrongQuestion",
        ],
    ),
    (
        "Tasks",
        [
            "BackgroundJob",
        ],
    ),
]


@register.simple_tag
def get_admin_categories(app_list: list[dict]) -> list[dict]:
    models: list[dict] = []
    for app in app_list:
        for model in app.get("models", []):
            models.append(model)

    model_lookup = {model.get("object_name"): model for model in models}
    used = set()
    categories: list[dict] = []

    for title, model_names in CATEGORY_ORDER:
        bucket = []
        for model_name in model_names:
            model = model_lookup.get(model_name)
            if model:
                bucket.append(model)
                used.add(model_name)
        if bucket:
            categories.append({"title": title, "models": bucket})

    leftovers = [model for model in models if model.get("object_name") not in used]
    if leftovers:
        categories.append({"title": "Other", "models": sorted(leftovers, key=lambda item: item.get("name", ""))})

    return categories
