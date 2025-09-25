# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class IsFirebaseAuthenticated(BasePermission):
#     message = "Authentication required"
#     def has_permission(self, request, view):
#         return bool(getattr(request, "uid", None))

# class IsOwnerOrAdmin(BasePermission):
#     message = "Forbidden"
#     def _is_admin(self, request):
#         try:
#             return (request.user_profile or {}).get("role") == "admin"
#         except Exception:
#             return False
#     def _is_owner(self, request, obj):
#         # obj is DfitUser
#         return getattr(request, "uid", None) == getattr(obj, "firebase_uid", None)
#     def has_object_permission(self, request, view, obj):
#         return self._is_owner(request, obj) or self._is_admin(request)

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