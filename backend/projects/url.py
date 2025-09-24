# projects/urls.py
from django.urls import path
from .views import ProjectViewSet

urlpatterns = [
    # Map the 'list' method in the ViewSet to GET /api/projects/list/
    path('list/', ProjectViewSet.as_view({'get': 'list'}), name='project-list'),
    
    # Map the 'create' method to POST /api/projects/create/
    path('create/', ProjectViewSet.as_view({'post': 'create'}), name='project-create'),
    
    # Map the 'upload_file' method to POST /api/projects/upload_file/
    path('upload_file/', ProjectViewSet.as_view({'post': 'upload_file'}), name='project-upload-file'),
    
    # Map the 'retrieve' method to GET /api/projects/get/<pk>/
    path('get/<int:pk>/', ProjectViewSet.as_view({'get': 'retrieve'}), name='project-get-detail'),

    path('<int:pk>/generate_content/', ProjectViewSet.as_view({'post': 'generate_content'}), name='project-generate-content'),
    
    # You could also add update and delete like this later
    # path('update/<int:pk>/', ProjectViewSet.as_view({'put': 'update'}), name='project-update'),
    path('delete/<int:pk>/', ProjectViewSet.as_view({'delete': 'destroy'}), name='project-delete'),
]