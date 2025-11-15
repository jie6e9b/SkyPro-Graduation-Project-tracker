"""Admin configuration for timelogs app."""
from django.contrib import admin
from .models import TimeLog


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    """Admin interface for TimeLog model."""

    list_display = (
        'id',
        'user',
        'task',
        'task_item',
        'date',
        'hours',
        'created_at'
    )
    list_filter = (
        'date',
        'user',
        'task__status',
        'created_at'
    )
    search_fields = (
        'description',
        'user__email',
        'user__first_name',
        'user__last_name',
        'task__title'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user', 'task', 'task_item')
    date_hierarchy = 'date'

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'task', 'task_item')
        }),
        ('Временные данные', {
            'fields': ('date', 'hours', 'description')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'task', 'task_item')
