from django.urls import path, include
from fitproject.views import user_list, user_detail, create_profile

urlpatterns = [
    path('create-profile/', create_profile, name='create-profile'),
    path('users/', user_list.as_view(), name='user-list'),
    path('users/<str:firebase_uid>/', user_detail.as_view(), name='user-detail'),
]
