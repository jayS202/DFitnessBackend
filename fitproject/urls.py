from django.urls import path
from .views import get_my_profile, set_user_role, get_user_data, create_profile, check_custom_claims, login

urlpatterns = [
    path("me/", get_my_profile),
    path("set-role/", set_user_role),
    path("get-user/", get_user_data),
    path("create-profile/", create_profile),
    path("check-claims/", check_custom_claims),
    path("login/", login)
]