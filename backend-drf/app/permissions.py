from rest_framework.permissions import BasePermission


class IsAuthenticatedJWT(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "id", None))


class IsAdminRole(IsAuthenticatedJWT):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return getattr(request.user, "role", None) == "admin"


class IsCoachRole(IsAuthenticatedJWT):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return getattr(request.user, "role", None) == "coach"
