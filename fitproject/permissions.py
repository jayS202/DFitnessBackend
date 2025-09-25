from rest_framework.permissions import BasePermission

class IsSessionAuthenticated(BasePermission):
    message = "Authentication required"
    def has_permission(self, request, view):
        return bool(getattr(request, "uid", None))

class UserAccessPermission(BasePermission):
    message = "Forbidden"
    def has_object_permission(self, request, view, obj):
        role = (request.user_profile or {}).get("role")
        is_admin = role == "admin"
        is_owner = getattr(obj, "firebase_uid", None) == getattr(request, "uid", None)
        m = request.method.upper()
        if m == "DELETE":
            return is_admin
        if m in ("PUT", "PATCH"):
            return is_owner or is_admin
        if m == "GET":
            return is_owner or is_admin
        return False