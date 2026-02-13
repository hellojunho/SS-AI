from django.urls import include, path

from app.views_root import root

urlpatterns = [
    path("", root),
    path("", include("app.urls")),
]
