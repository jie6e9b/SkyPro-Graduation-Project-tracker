"""Serializers for tasks app."""
from rest_framework import serializers
from django.db import transaction
from apps.users.serializers import UserSerializer
from .models import Task, TaskRole, TaskItem


class TaskRoleSerializer(serializers.ModelSerializer):
    """Serializer for TaskRole model."""
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = TaskRole
        fields = ('id', 'user', 'user_id', 'role', 'role_display', 'assigned_at')
        read_only_fields = ('id', 'assigned_at')


class TaskItemSerializer(serializers.ModelSerializer):
    """Serializer for TaskItem model."""
    
    executor = UserSerializer(read_only=True)
    executor_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    spent_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = TaskItem
        fields = (
            'id',
            'title',
            'description',
            'executor',
            'executor_id',
            'status',
            'status_display',
            'planned_hours',
            'spent_hours',
            'order',
            'completed_at',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'completed_at', 'created_at', 'updated_at')


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for Task list (summary view)."""
    
    assigner = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    task_items_count = serializers.SerializerMethodField()
    completed_items_count = serializers.SerializerMethodField()
    total_planned_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_spent_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'progress_percentage',
            'planned_start_date',
            'planned_end_date',
            'actual_start_date',
            'actual_end_date',
            'assigner',
            'task_items_count',
            'completed_items_count',
            'total_planned_hours',
            'total_spent_hours',
            'created_at',
            'updated_at'
        )
    
    def get_task_items_count(self, obj):
        """Get total number of task items."""
        return obj.items.count()
    
    def get_completed_items_count(self, obj):
        """Get number of completed task items."""
        return obj.items.filter(status='completed').count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for Task detail view."""
    
    roles = TaskRoleSerializer(many=True, read_only=True)
    items = TaskItemSerializer(many=True, read_only=True, source='items.all')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_planned_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_spent_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    assigner = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'source_links',
            'result_link',
            'status',
            'status_display',
            'planned_start_date',
            'actual_start_date',
            'planned_end_date',
            'actual_end_date',
            'progress_percentage',
            'total_planned_hours',
            'total_spent_hours',
            'assigner',
            'roles',
            'items',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new task with roles and items."""
    
    co_executors = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text='List of user IDs for co-executors'
    )
    observers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text='List of user IDs for observers'
    )
    task_items = TaskItemSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'source_links',
            'result_link',
            'planned_start_date',
            'planned_end_date',
            'co_executors',
            'observers',
            'task_items'
        )
        read_only_fields = ('id',)
    
    @transaction.atomic
    def create(self, validated_data):
        """Create task with roles and items."""
        co_executors = validated_data.pop('co_executors', [])
        observers = validated_data.pop('observers', [])
        task_items_data = validated_data.pop('task_items', [])
        
        # Create task
        task = Task.objects.create(**validated_data)
        
        # Create assigner role for current user
        TaskRole.objects.create(
            task=task,
            user=self.context['request'].user,
            role='assigner'
        )
        
        # Create co-executor roles
        for user_id in co_executors:
            TaskRole.objects.create(
                task=task,
                user_id=user_id,
                role='co_executor'
            )
        
        # Create observer roles
        for user_id in observers:
            TaskRole.objects.create(
                task=task,
                user_id=user_id,
                role='observer'
            )
        
        # Create task items
        for idx, item_data in enumerate(task_items_data):
            executor_id = item_data.pop('executor_id', None)
            TaskItem.objects.create(
                task=task,
                executor_id=executor_id,
                order=idx,
                **item_data
            )
        
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a task."""
    
    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'source_links',
            'result_link',
            'status',
            'planned_start_date',
            'actual_start_date',
            'planned_end_date',
            'actual_end_date'
        )
    
    def validate_status(self, value):
        """Validate that all items are completed before marking task as completed."""
        task = self.instance
        if value == 'completed' and task:
            incomplete_items = task.items.exclude(status='completed')
            if incomplete_items.exists():
                raise serializers.ValidationError(
                    f'Невозможно завершить задачу. '
                    f'Есть незавершенные подзадачи: {incomplete_items.count()}'
                )
        return value
