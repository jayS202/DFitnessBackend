from firebase_admin import auth as firebase_auth, firestore
from django.conf import settings
from .firebase_admin_init import fs_db, firebase_app
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .decorators import require_roles
import datetime
import os

from fitproject.models import DfitUser, Profile
from .serializers import UserSerializer, ProfileSerializer
from .permissions import IsSessionAuthenticated, UserAccessPermission

from rest_framework.views import APIView
from rest_framework import generics

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
def set_user_role(request):
    data = request.data
    target = data.get("uid")
    role = data.get("role")
    perms = data.get("permissions", [])
    admin_uid = data.get("adminUid", "")

    if not target or not role:
        return Response({"detail": "uid & role required"}, status=400)
    
    try:
        target_user = firebase_auth.get_user(target)
    except firebase_auth.UserNotFoundError:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    user_ref = fs_db.collection("users").document(target)

    user_ref.set({
        "role": role,
        "permissions": perms,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "updatedBy": admin_uid
    }, merge=True)

    firebase_auth.set_custom_user_claims(target, {"role": role, "permissions": perms})
    
    try:
        firebase_auth.revoke_refresh_tokens(target)
    except Exception:
        pass
    
    return Response(
        {
            "uid": target,
            "role": role,
            "permissions": perms,
            "updatedBy": admin_uid,
            "email": getattr(target_user, "email", None)
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
def create_profile(request):
    """
    Client calls this immediately after signup.
    Expects Authorization: Bearer <idToken> and body { uid, email }.
    Ensures the authenticated request.uid matches the target uid before creating profile
    and setting custom claims (role).
    """
    if not request.uid:
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    target = data.get("uid")
    email = data.get("email")
    first_name = data.get("first_name") or ""
    last_name = data.get("last_name")or ""
    if not target or request.uid != target:
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
    try:
        # set server-side custom claims
        firebase_auth.set_custom_user_claims(target, {"role": "customer", "permissions": []})
        
        db = firestore.client()
        db.collection("users").document(target).set(
            {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "role": "customer",
                "permissions": [],
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "createdBy": target,
                "updatedBy": target,
            },
            merge=True
        )
        
        return Response({"status": "profile_created", "role": "customer"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print("Error in create_profile:", str(e))
        return Response({"detail": "Profile creation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        secure_flag = bool(os.environ.get("SESSION_COOKIE_SECURE", True))
        if remember:
            expires_in = datetime.timedelta(days=5)
            session_cookie =  firebase_auth.create_session_cookie(token, expires_in=expires_in)
            resp = Response(res_body, status=status.HTTP_200_OK)
            resp.set_cookie(
                "session", 
                session_cookie, 
                max_age=int(expires_in.total_seconds()),
                httponly=True,
                secure=secure_flag,
                samesite='Lax'
            )
            print("Session cookie set:", resp.cookies)
            return resp
        return Response(res_body, status=status.HTTP_200_OK)        
    except Exception as e:
        print("Error verifying ID token:", str(e))
        return Response({"detail": "Invalid ID token or login failed", "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
def verify_session(request):
    session = request.COOKIES.get("session")
    if not session:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Bearer"):
            session = header.split(" ", 1)[1]
            
    if not session:
        return Response({"detail": "No session provided"}, status = status.HTTP_400_BAD_REQUEST)
    
    try:
        decoded = firebase_auth.verify_session_cookie(session, check_revoked=True)
        role = decoded.get("role") or decoded.get("customClaims", {}).get("role") or "customer"

        return Response({"uid": decoded.get("uid"), "role": role}, status=status.HTTP_200_OK)
    except firebase_auth.RevokedIdTokenError:
        return Response({"detail": "Session revoked, please login again"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"detail": "Invalid session", "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    
############### User CRUD Views ###############
class user_list(APIView):
    permission_classes = [IsSessionAuthenticated]
    
    def get_permissions(self):
        if self.request.method == "POST":
            return []
        return [perm() for perm in self.permission_classes]
    
    def get(self, request):
        users = DfitUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class user_detail(APIView):
    permission_classes = [IsSessionAuthenticated, UserAccessPermission]
    def get(self, request, firebase_uid):
        try:
            user = DfitUser.objects.get(firebase_uid=firebase_uid)
        except DfitUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, firebase_uid):
        user = DfitUser.objects.get(firebase_uid=firebase_uid)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, firebase_uid):
        user = DfitUser.objects.get(firebase_uid=firebase_uid)
        user.delete()
        return Response("User deleted successfully",status=status.HTTP_204_NO_CONTENT)  
    

class profile_list(APIView):
    permission_classes = [IsSessionAuthenticated]
    
    # def get_permissions(self):
    #     if self.request.method == "POST":
    #         return []
    #     return [perm() for perm in self.permission_classes]
    
    def get(self, request):
        profiles = Profile.objects.select_related("user").all()
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)

    def post(self, request):
        firebase_uid = request.data.get("firebase_uid")
        if not firebase_uid:
            return Response({"error": "Firebase UID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = DfitUser.objects.get(firebase_uid=firebase_uid)
        except DfitUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        profile, _ = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class profile_detail(APIView):
    permission_classes = [IsSessionAuthenticated, UserAccessPermission]
    def get(self, request, firebase_uid):
        try:
            profile = Profile.objects.select_related("user").get(user__firebase_uid=firebase_uid)
        except Profile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, firebase_uid):
        try:
            profile = Profile.objects.select_related("user").get(user__firebase_uid=firebase_uid)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, firebase_uid):
        try:
            profile = Profile.objects.get(user__firebase_uid=firebase_uid)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        profile.delete()
        return Response("Profile deleted successfully",status=status.HTTP_204_NO_CONTENT)  

