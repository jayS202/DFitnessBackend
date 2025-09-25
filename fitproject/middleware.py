# from django.utils.deprecation import MiddlewareMixin
# from django.conf import settings
# from .firebase_admin_init import fs_db
# from firebase_admin import auth as firebase_auth

# # class FirebaseAuthMiddleware(MiddlewareMixin):
# #     def process_request(self, request):
# #         header = request.META.get("HTTP_AUTHORIZATION", "")
# #         uid = None
# #         profile = {}
# #         if header.startswith("Bearer "):
# #             token = header.split(" ", 1)[1]
# #             try:
# #                 decoded = firebase_auth.verify_id_token(token)
# #                 uid = decoded.get("uid")
# #                 # doc = settings.fs_db.collection("users").document(uid).get()
# #                 doc = fs_db.collection("users").document(uid).get()
# #                 profile = doc.to_dict() or {}
# #                 print("[FirebaseAuthMiddleware] Authenticated uid:", uid)
# #                 print("[FirebaseAuthMiddleware] profile:", profile)
# #             except Exception as e:
# #                 print("[FirebaseAuthMiddleware] token verification failed: ", str(e))
# #                 pass
# #         request.uid = uid
# #         request.user_profile = profile


# from django.utils.deprecation import MiddlewareMixin
# from firebase_admin import auth as firebase_auth
# from .firebase_admin_init import fs_db

# class FirebaseAuthMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         request.uid = None
#         request.user_profile = {}

#         session_cookie = request.COOKIES.get("session")
#         auth_header = request.META.get("HTTP_AUTHORIZATION", "")
#         bearer_token = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else None

#         decoded = None
#         uid = None
#         profile = {}

#         # 1. Prefer session cookie
#         if session_cookie:
#             try:
#                 decoded = firebase_auth.verify_session_cookie(session_cookie, check_revoked=True)
#                 uid = decoded.get("uid")
#                 print("[FirebaseAuthMiddleware] session cookie OK uid:", uid)
#             except Exception as e:
#                 print("[FirebaseAuthMiddleware] session cookie invalid:", e)

#         # 2. Fallback to ID token in header
#         if not uid and bearer_token:
#             try:
#                 decoded = firebase_auth.verify_id_token(bearer_token)
#                 uid = decoded.get("uid")
#                 print("[FirebaseAuthMiddleware] bearer ID token OK uid:", uid)
#             except Exception as e:
#                 print("[FirebaseAuthMiddleware] bearer token invalid:", e)

#         if uid:
#             # Try Firestore doc for role / profile fields
#             try:
#                 doc = fs_db.collection("users").document(uid).get()
#                 profile = doc.to_dict() or {}
#             except Exception as e:
#                 print("[FirebaseAuthMiddleware] Firestore fetch failed:", e)
#             # Merge custom claims if role missing
#             if decoded:
#                 claims_role = (decoded.get("role")
#                                or (decoded.get("customClaims") or {}).get("role"))
#                 if claims_role and "role" not in profile:
#                     profile["role"] = claims_role

#         request.uid = uid
#         request.user_profile = profile


from django.utils.deprecation import MiddlewareMixin
from firebase_admin import auth as firebase_auth
from .firebase_admin_init import fs_db
import base64
import json

class FirebaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.uid = None
        request.user_profile = {}

        session_cookie = request.COOKIES.get("session")
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        bearer_token = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else None

        decoded_claims = None
        uid = None
        profile = {}

        def decode_header_part(jwt_token):
            try:
                parts = jwt_token.split(".")
                if len(parts) < 2:
                    return {}
                payload = parts[1] + "=" * (-len(parts[1]) % 4)
                return json.loads(base64.urlsafe_b64decode(payload.encode() or b"{}"))
            except Exception:
                return {}

        # 1. Prefer session cookie
        if session_cookie and not uid:
            try:
                decoded_claims = firebase_auth.verify_session_cookie(session_cookie, check_revoked=True)
                uid = decoded_claims.get("uid")
                print("[AuthMW] session cookie OK uid:", uid)
            except Exception as e:
                print("[AuthMW] session cookie invalid:", e)

        # 2. Bearer: try ID token
        if bearer_token and not uid:
            try:
                decoded_claims = firebase_auth.verify_id_token(bearer_token)
                uid = decoded_claims.get("uid")
                print("[AuthMW] bearer ID token OK uid:", uid)
            except Exception as e_id:
                # Check issuer hint
                payload_preview = decode_header_part(bearer_token)
                iss = payload_preview.get("iss", "")
                if "session.firebase.google.com" in iss:
                    try:
                        decoded_claims = firebase_auth.verify_session_cookie(bearer_token, check_revoked=True)
                        uid = decoded_claims.get("uid")
                        print("[AuthMW] bearer value treated as session cookie uid:", uid)
                    except Exception as e_sess:
                        print("[AuthMW] bearer session verify failed:", e_id, "|", e_sess)
                else:
                    print("[AuthMW] bearer token invalid:", e_id)

        if uid:
            try:
                doc = fs_db.collection("users").document(uid).get()
                profile = doc.to_dict() or {}
            except Exception as e:
                print("[AuthMW] Firestore fetch failed:", e)
            # merge custom claims role if missing
            if decoded_claims:
                role = decoded_claims.get("role") or (decoded_claims.get("customClaims") or {}).get("role")
                if role and "role" not in profile:
                    profile["role"] = role

        request.uid = uid
        request.user_profile = profile