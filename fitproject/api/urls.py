from django.urls import path, include
from fitproject.views import user_list, user_detail, create_profile, set_user_role, login, verify_session, profile_list, profile_detail

urlpatterns = [
    path('login/', login, name='login'),
    path('create-profile/', create_profile, name='create-profile'),
    path('set-role/', set_user_role, name='set-role'),
    path('verify-session/', verify_session, name='verify-session'),
    path('users/', user_list.as_view(), name='user-list'),
    path('users/<str:firebase_uid>/', user_detail.as_view(), name='user-detail'),
    path('profile/', profile_list.as_view(), name='profile-list'),
    path('profile/<str:firebase_uid>/', profile_detail.as_view(), name='profile-detail'),
]
