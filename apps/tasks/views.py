"""Views for tasks app."""
from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q

from .models import Task, TaskRole, TaskItem
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskRoleSerializer,
    TaskItemSerializer,
)
from .permissions import IsTaskParticipant, IsAssigner, IsTaskItemExecutorOrAssigner
from .filters import TaskFilter, TaskItemFilter


@extend_schema_view(
    list=extend_schema(
        tags=['Tasks'],
        summary='Список задач',
        description='Получить список задач с фильтрацией'
    ),
    retrieve=extend_schema(
        tags=['Tasks'],
        summary='Детали задачи',
        description='Получить детальную информацию о задаче'
    ),
    create=extend_schema(
        tags=['Tasks'],
        summary='Создать задачу',
        description='Создать новую задачу с подзадачами и ролями'
    ),
    update=extend_schema(
        tags=['Tasks'],
        summary='Обновить задачу',
        description='Обновить всю задачу (PUT)'
    ),
    partial_update=extend_schema(
        tags=['Tasks'],
        summary='Частично обновить задачу',
        description='Частично обновить задачу (PATCH)'
    ),
    destroy=extend_schema(
        tags=['Tasks'],
        summary='Удалить задачу',
        description='Удалить задачу (только постановщик)'
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task model."""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    
    def get_queryset(self):
        """Get queryset with optimized queries."""
        return Task.objects.select_related().prefetch_related(
            'roles__user',
            'items__executor'
        ).filter(
            Q(roles__user=self.request.user) | Q(items__executor=self.request.user)
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskDetailSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAssigner()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), IsTaskParticipant()]
        elif self.action == 'list':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create task and set current user as assigner."""
        serializer.save()
    
    @extend_schema(
        tags=['Tasks'],
        summary='Мои задачи',
        description='Получить список задач, где я участник (любая роль)'
    )
    @decorators.action(detail=False, methods=['get'])
    def my(self, request):
        """Get tasks where current user is participant."""
        tasks = self.get_queryset().filter(
            Q(roles__user=request.user) | Q(items__executor=request.user)
        ).distinct()
        
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Tasks'],
        summary='Мои подзадачи',
        description='Получить список подзадач, где я исполнитель'
    )
    @decorators.action(detail=False, methods=['get'])
    def my_items(self, request):
        """Get task items where current user is executor."""
        items = TaskItem.objects.filter(executor=request.user).select_related('task')
        serializer = TaskItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Tasks'],
        summary='Назначенные мной',
        description='Получить список задач, где я постановщик'
    )
    @decorators.action(detail=False, methods=['get'])
    def assigned_by_me(self, request):
        """Get tasks where current user is assigner."""
        tasks = Task.objects.filter(roles__user=request.user, roles__role='assigner')
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Tasks'],
        summary='Добавить роль',
        description='Добавить участника к задаче (только постановщик)',
        request=TaskRoleSerializer,
        responses={201: TaskRoleSerializer}
    )
    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAssigner])
    def add_role(self, request, pk=None):
        """Add a role to the task."""
        task = self.get_object()
        serializer = TaskRoleSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Tasks'],
        summary='Удалить роль',
        description='Удалить участника из задачи (только постановщик)',
        responses={204: None}
    )
    @decorators.action(
        detail=True,
        methods=['delete'],
        url_path='roles/(?P<role_id>[^/.]+)',
        permission_classes=[IsAuthenticated, IsAssigner]
    )
    def remove_role(self, request, pk=None, role_id=None):
        """Remove a role from the task."""
        task = self.get_object()
        
        try:
            role = TaskRole.objects.get(pk=role_id, task=task)
            
            # Cannot remove assigner role
            if role.role == 'assigner':
                return Response(
                    {'detail': 'Нельзя удалить роль постановщика'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaskRole.DoesNotExist:
            return Response(
                {'detail': 'Роль не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        tags=['Tasks'],
        summary='Добавить подзадачу',
        description='Добавить подзадачу к задаче (только постановщик)',
        request=TaskItemSerializer,
        responses={201: TaskItemSerializer}
    )
    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAssigner])
    def add_item(self, request, pk=None):
        """Add a task item to the task."""
        task = self.get_object()
        serializer = TaskItemSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        tags=['Task Items'],
        summary='Список подзадач',
        description='Получить список подзадач с фильтрацией'
    ),
    retrieve=extend_schema(
        tags=['Task Items'],
        summary='Детали подзадачи'
    ),
    update=extend_schema(
        tags=['Task Items'],
        summary='Обновить подзадачу'
    ),
    partial_update=extend_schema(
        tags=['Task Items'],
        summary='Частично обновить подзадачу'
    ),
    destroy=extend_schema(
        tags=['Task Items'],
        summary='Удалить подзадачу'
    ),
)
class TaskItemViewSet(viewsets.ModelViewSet):
    """ViewSet for TaskItem model."""
    
    serializer_class = TaskItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskItemFilter
    
    def get_queryset(self):
        """Get queryset filtered by user access."""
        # User can see items from tasks they participate in
        return TaskItem.objects.filter(
            Q(task__roles__user=self.request.user) | Q(executor=self.request.user)
        ).select_related('task', 'executor').distinct()
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTaskItemExecutorOrAssigner()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), IsTaskParticipant()]
        return [IsAuthenticated()]
