"""URLs for tasks app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskItemViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-items', TaskItemViewSet, basename='taskitem')

urlpatterns = [
    path('', include(router.urls)),
]
