from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsFirebaseAuthenticated(BasePermission):
    message = "Authentication required"
    def has_permission(self, request, view):
        return bool(getattr(request, "uid", None))

class IsOwnerOrAdmin(BasePermission):
    message = "Forbidden"
    def _is_admin(self, request):
        try:
            return (request.user_profile or {}).get("role") == "admin"
        except Exception:
            return False
    def _is_owner(self, request, obj):
        # obj is DfitUser
        return getattr(request, "uid", None) == getattr(obj, "firebase_uid", None)
    def has_object_permission(self, request, view, obj):
        return self._is_owner(request, obj) or self._is_admin(request)