from rest_framework.response import Response
from rest_framework import status

def require_roles(*allowed_roles):
    def decorator(fn):
        def wrapper(request, *args, **kwargs):
            role = request.user_profile.get("role")
            if role not in allowed_roles:
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            return fn(request, *args, **kwargs)
        return wrapper
    return decorator