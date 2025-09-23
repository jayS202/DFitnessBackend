from django.urls import path, include
from fitproject.views import user_list, user_detail, create_profile, login, verify_session

urlpatterns = [
    path('login/', login, name='login'),
    path('create-profile/', create_profile, name='create-profile'),
    path('verify-session/', verify_session, name='verify-session'),
    path('users/', user_list.as_view(), name='user-list'),
    path('users/<str:firebase_uid>/', user_detail.as_view(), name='user-detail'),
]
