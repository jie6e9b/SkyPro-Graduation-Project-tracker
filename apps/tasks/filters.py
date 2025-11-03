"""Filters for tasks app."""
import django_filters
from django.db import models
from .models import Task, TaskItem


class TaskFilter(django_filters.FilterSet):
    """Filter for Task model."""
    
    status = django_filters.ChoiceFilter(choices=Task.STATUS_CHOICES)
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    planned_end_after = django_filters.DateFilter(field_name='planned_end_date', lookup_expr='gte')
    planned_end_before = django_filters.DateFilter(field_name='planned_end_date', lookup_expr='lte')
    
    # Filter by assigner
    assigner = django_filters.NumberFilter(method='filter_by_assigner')
    
    # Filter by executor (in any task item)
    executor = django_filters.NumberFilter(method='filter_by_executor')
    
    # Filter by participation (user has any role or is executor)
    my_tasks = django_filters.BooleanFilter(method='filter_my_tasks')
    
    # Filter overdue tasks
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    
    class Meta:
        model = Task
        fields = ['status']
    
    def filter_by_assigner(self, queryset, name, value):
        """Filter by assigner user ID."""
        return queryset.filter(roles__user_id=value, roles__role='assigner')
    
    def filter_by_executor(self, queryset, name, value):
        """Filter by executor in any task item."""
        return queryset.filter(items__executor_id=value).distinct()
    
    def filter_my_tasks(self, queryset, name, value):
        """Filter tasks where current user is participant."""
        if not value:
            return queryset
        
        user = self.request.user
        # Tasks where user has role OR is executor of any item
        return queryset.filter(
            models.Q(roles__user=user) | models.Q(items__executor=user)
        ).distinct()
    
    def filter_overdue(self, queryset, name, value):
        """Filter overdue tasks."""
        from django.utils import timezone
        
        if not value:
            return queryset
        
        today = timezone.now().date()
        return queryset.filter(
            planned_end_date__lt=today,
            status__in=['new', 'in_progress', 'review']
        )


class TaskItemFilter(django_filters.FilterSet):
    """Filter for TaskItem model."""
    
    status = django_filters.ChoiceFilter(choices=TaskItem.STATUS_CHOICES)
    executor = django_filters.NumberFilter(field_name='executor_id')
    task = django_filters.NumberFilter(field_name='task_id')
    my_items = django_filters.BooleanFilter(method='filter_my_items')
    
    class Meta:
        model = TaskItem
        fields = ['status', 'executor', 'task']
    
    def filter_my_items(self, queryset, name, value):
        """Filter items where current user is executor."""
        if not value:
            return queryset
        
        return queryset.filter(executor=self.request.user)
