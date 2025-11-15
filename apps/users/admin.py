"""Admin configuration for users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ('email', 'first_name', 'last_name', 'position', 'department', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'department')
    search_fields = ('email', 'first_name', 'last_name', 'position', 'department')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'position', 'department')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
