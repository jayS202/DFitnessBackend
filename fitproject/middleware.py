from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .firebase_admin_init import fs_db
from firebase_admin import auth as firebase_auth

class FirebaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        uid = None
        profile = {}
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1]
            try:
                decoded = firebase_auth.verify_id_token(token)
                uid = decoded.get("uid")
                # doc = settings.fs_db.collection("users").document(uid).get()
                doc = fs_db.collection("users").document(uid).get()
                profile = doc.to_dict() or {}
            except Exception:
                pass
        request.uid = uid
        request.user_profile = profile