from django.contrib import admin
from django.urls import include, path

from app.views_root import root

urlpatterns = [
    path("", root),
    path("admin/admin", admin.site.urls),
    path("", include("app.urls")),
]
