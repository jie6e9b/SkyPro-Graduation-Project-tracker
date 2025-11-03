"""Permissions for tasks app."""
from rest_framework import permissions


class IsTaskParticipant(permissions.BasePermission):
    """
    Permission to check if user is a participant in the task.
    
    A participant is:
    - Assigner (task creator)
    - Co-executor
    - Observer
    - Executor of any task item
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user has access to this task."""
        # Staff users can access everything
        if request.user.is_staff:
            return True

        # Handle TaskItem objects - check permission on parent task
        if hasattr(obj, 'task'):
            # This is a TaskItem, check task permissions
            task = obj.task
            has_role = task.roles.filter(user=request.user).exists()
            if has_role:
                return True
            is_executor = task.items.filter(executor=request.user).exists()
            if is_executor:
                return True
        else:
            # This is a Task object
            has_role = obj.roles.filter(user=request.user).exists()
            if has_role:
                return True
            is_executor = obj.items.filter(executor=request.user).exists()
            if is_executor:
                return True

        return False


class IsAssigner(permissions.BasePermission):
    """
    Permission to check if user is the task assigner (creator).
    
    Only the assigner can:
    - Update task details
    - Delete task
    - Add/remove roles
    - Add/remove task items
    - Change task item executors
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the task assigner."""
        # Staff users can do everything
        if request.user.is_staff:
            return True

        # Handle TaskItem objects - check permission on parent task
        if hasattr(obj, 'task'):
            # This is a TaskItem, check task assigner
            assigner_role = obj.task.roles.filter(user=request.user, role='assigner').exists()
        else:
            # This is a Task object
            assigner_role = obj.roles.filter(user=request.user, role='assigner').exists()

        return assigner_role


class IsTaskItemExecutorOrAssigner(permissions.BasePermission):
    """
    Permission to check if user can modify a task item.
    
    Can modify:
    - Task assigner (can do everything)
    - Task item executor (can change status, add time logs)
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can modify this task item."""
        # Staff users can do everything
        if request.user.is_staff:
            return True
        
        # Check if user is the task assigner
        is_assigner = obj.task.roles.filter(user=request.user, role='assigner').exists()
        if is_assigner:
            return True
        
        # Check if user is the executor of this item
        if obj.executor == request.user:
            # Executor can only update status and add time logs
            if request.method in ['PATCH', 'PUT']:
                # Check if only allowed fields are being updated
                allowed_fields = {'status'}
                update_fields = set(request.data.keys())
                if update_fields.issubset(allowed_fields):
                    return True
            return False
        
        return False


class CanCreateTask(permissions.BasePermission):
    """
    Permission to check if user can create tasks.
    
    All authenticated users can create tasks.
    """
    
    def has_permission(self, request, view):
        """Check if user can create a task."""
        return request.user and request.user.is_authenticated
