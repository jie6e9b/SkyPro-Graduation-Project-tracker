"""Admin configuration for tasks app."""
from django.contrib import admin
from .models import Task, TaskRole, TaskItem


class TaskRoleInline(admin.TabularInline):
    """Inline for task roles."""
    model = TaskRole
    extra = 1
    autocomplete_fields = ['user']


class TaskItemInline(admin.TabularInline):
    """Inline for task items."""
    model = TaskItem
    extra = 1
    autocomplete_fields = ['executor']
    fields = ('title', 'executor', 'status', 'planned_hours', 'order')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""
    
    list_display = (
        'title',
        'status',
        'get_assigner',
        'progress_percentage',
        'planned_end_date',
        'created_at'
    )
    list_filter = ('status', 'created_at', 'planned_end_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'progress_percentage', 'total_planned_hours', 'total_spent_hours')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'status')
        }),
        ('Ссылки', {
            'fields': ('source_links', 'result_link')
        }),
        ('Даты', {
            'fields': (
                'planned_start_date',
                'actual_start_date',
                'planned_end_date',
                'actual_end_date'
            )
        }),
        ('Статистика', {
            'fields': ('progress_percentage', 'total_planned_hours', 'total_spent_hours'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskRoleInline, TaskItemInline]
    
    def get_assigner(self, obj):
        """Get task assigner."""
        assigner = obj.assigner
        return assigner.get_full_name() if assigner else '-'
    get_assigner.short_description = 'Постановщик'


@admin.register(TaskRole)
class TaskRoleAdmin(admin.ModelAdmin):
    """Admin interface for TaskRole model."""
    
    list_display = ('task', 'user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('task__title', 'user__email', 'user__first_name', 'user__last_name')
    autocomplete_fields = ['task', 'user']


@admin.register(TaskItem)
class TaskItemAdmin(admin.ModelAdmin):
    """Admin interface for TaskItem model."""
    
    list_display = (
        'title',
        'task',
        'executor',
        'status',
        'planned_hours',
        'spent_hours',
        'order'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'task__title')
    autocomplete_fields = ['task', 'executor']
    readonly_fields = ('spent_hours', 'created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('task', 'title', 'description', 'executor')
        }),
        ('Статус и трудоемкость', {
            'fields': ('status', 'planned_hours', 'spent_hours', 'order')
        }),
        ('Даты', {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
