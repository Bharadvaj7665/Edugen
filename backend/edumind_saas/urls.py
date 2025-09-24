# edumind_saas/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.views import ProjectViewSet , GeneratedContentViewSet
from chat.views import ChatSessionViewSet
from users import urls

# Create a router and register our ViewSet
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'chat-sessions', ChatSessionViewSet, basename='chatsession')
router.register(r'content', GeneratedContentViewSet, basename='content')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('api/', include(router.urls)), # Use the router for all API endpoints
    path('api/projects/delete/<int:pk>/', ProjectViewSet.as_view({'delete': 'destroy'}), name='project-delete'),
    path('api/users/', include('users.urls')),
]