# users/urls.py
from django.urls import path
from .views import UserProfileAPIView

urlpatterns = [
    path('me/', UserProfileAPIView.as_view(), name='user-profile'),
]