# import firestore as _  # avoid clash
from firebase_admin import auth as firebase_auth, firestore
from django.conf import settings
from .firebase_admin_init import fs_db, firebase_app
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .decorators import require_roles
import datetime

@api_view(["GET"])
def get_my_profile(request):
    if not request.uid:
        return Response({"detail": "Unauthorized"}, status=401)
    return Response(request.user_profile)

@api_view(["POST"])
def get_user_data(request):
    data = request.data
    target = data.get("uid")
    if not target:
        return Response({"detail": "uid required"}, status=400)
    user_ref = fs_db.collection("users").document(target)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return Response({"detail": "User not found"}, status=404)
    return Response(user_doc.to_dict())

@api_view(["POST"])
# @require_roles("admin")
def set_user_role(request):
    data = request.data
    target = data.get("uid")
    role = data.get("role")
    perms = data.get("permissions", [])
    admin_uid = data.get("adminUid", "")

    if not target or not role:
        return Response({"detail": "uid & role required"}, status=400)

    user_ref = fs_db.collection("users").document(target)
    old = user_ref.get().to_dict() or {}
    old_role = old.get("role", "")

    user_ref.set({
        "role": role,
        "permissions": perms,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "updatedBy": admin_uid
    }, merge=True)

    # fs_db.collection("role_changes").document(target).add({
    #     "uid": target,
    #     "oldRole": old_role,
    #     "newRole": role,
    #     "changedBy": admin_uid,
    #     "timestamp": firestore.SERVER_TIMESTAMP
    # })

    firebase_auth.set_custom_user_claims(target, {"role": role, "permissions": perms})
    return Response({"status": "ok"})

@api_view(["POST"])
def create_profile(request):
    """
    Client calls this immediately after signup.
    Expects Authorization: Bearer <idToken> and body { uid, email }.
    Ensures the authenticated request.uid matches the target uid before creating profile
    and setting custom claims (role).
    """
    try:
        data = request.data
        target = data.get("uid")
        email = data.get("email")
        if not target or request.uid != target:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # set server-side custom claims
        firebase_auth.set_custom_user_claims(target, {"role": "customer", "permissions": []})
        print("Auth is Set!")
        return Response({'status': 'Custom claims is set'}, status=201)
    except Exception as e:
        print("Error in create_profile:", str(e))
        return Response({"error": "Setting Custom claims failed"}, status=500)


@api_view(["POST"])
def check_custom_claims(request):
    data = request.data
    uid = data.get("uid")
    if not uid:
        return Response({"detail": "uid required"}, status=400)
    user = firebase_auth.get_user(uid)
    print("user:", user.__dict__)
    res = {
        "email": user.email,
        "UID": user.uid,
        "customClaims": user.custom_claims
    }
    return Response(res)
        
@api_view(["POST"])
def login(request):
    """
    Accepts either:
      - JSON body { "tokenId": "<token>", "remember": true } 
      - OR Authorization: Bearer <token>

    Verifies the ID token, returns uid, email, custom claims and Firestore profile.
    If "remember" is true the view will mint a Firebase session cookie and set it
    as a secure HttpOnly cookie (requires HTTPS in production).
    """
    # get token from body or Authorization header
    token = request.data.get("tokenId")
    
    if not token:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Bearer "):
            token = header.split("Bearer ")[1]
    if not token:
        return Response({"detail": "TokenId required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        decoded = firebase_auth.verify_id_token(token)
        uid = decoded.get("uid")
        # fetch user record to get email and server-side custom claims
        user = firebase_auth.get_user(uid)
        custom_claims = user.custom_claims or {}
        
        # fetch Firestore profile if available
        profile = {}
        if fs_db:
            doc = fs_db.collection("users").document(uid).get()
            profile = doc.to_dict() or {}
            
        res_body = {
            "uid": uid,
            "email": user.email,
            "customClaims": custom_claims,
            "profile": profile
        }        
        
        # Mint Session Cookie for persistent server-side session
        remember = bool(request.data.get("remember", True))
        if remember:
            expires_in = datetime.timedelta(days=5)
            session_cookie =  firebase_auth.create_session_cookie(token, expires_in=expires_in)
            resp = Response(res_body, status=status.HTTP_200_OK)
            resp.set_cookie(
                "session", 
                session_cookie, 
                max_age=int(expires_in.total_seconds()),
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            print("Session cookie set:", resp.cookies)
            return resp
        return Response(res_body, status=status.HTTP_200_OK)        
    except Exception as e:
        print("Error verifying ID token:", str(e))
        return Response({"detail": "Invalid ID token or login failed", "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
