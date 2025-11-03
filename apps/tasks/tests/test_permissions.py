"""Tests for tasks app permissions."""
import pytest
from unittest.mock import Mock
from apps.tasks.permissions import (
    IsTaskParticipant,
    IsAssigner,
    IsTaskItemExecutorOrAssigner,
)
from apps.tasks.models import Task, TaskRole, TaskItem


@pytest.mark.django_db
class TestIsTaskParticipant:
    """Tests for IsTaskParticipant permission."""

    def test_assigner_has_permission(self, task, user):
        """Test that task assigner has permission."""
        request = Mock()
        request.user = user
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is True

    def test_co_executor_has_permission(self, task, user2):
        """Test that co-executor has permission."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is True

    def test_observer_has_permission(self, task, user2):
        """Test that observer has permission."""
        TaskRole.objects.create(task=task, user=user2, role='observer')

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is True

    def test_executor_has_permission(self, task, user2):
        """Test that task item executor has permission."""
        TaskItem.objects.create(
            task=task,
            title='Test Item',
            executor=user2
        )

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is True

    def test_non_participant_no_permission(self, task, user2):
        """Test that non-participant has no permission."""
        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is False

    def test_staff_user_has_permission(self, task, user2):
        """Test that staff user always has permission."""
        user2.is_staff = True
        user2.save()

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsTaskParticipant()
        assert permission.has_object_permission(request, view, task) is True


@pytest.mark.django_db
class TestIsAssigner:
    """Tests for IsAssigner permission."""

    def test_assigner_has_permission(self, task, user):
        """Test that task assigner has permission."""
        request = Mock()
        request.user = user
        view = Mock()

        permission = IsAssigner()
        assert permission.has_object_permission(request, view, task) is True

    def test_co_executor_no_permission(self, task, user2):
        """Test that co-executor has no permission."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsAssigner()
        assert permission.has_object_permission(request, view, task) is False

    def test_observer_no_permission(self, task, user2):
        """Test that observer has no permission."""
        TaskRole.objects.create(task=task, user=user2, role='observer')

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsAssigner()
        assert permission.has_object_permission(request, view, task) is False

    def test_executor_no_permission(self, task, user2):
        """Test that task item executor has no permission."""
        TaskItem.objects.create(
            task=task,
            title='Test Item',
            executor=user2
        )

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsAssigner()
        assert permission.has_object_permission(request, view, task) is False

    def test_staff_user_has_permission(self, task, user2):
        """Test that staff user always has permission."""
        user2.is_staff = True
        user2.save()

        request = Mock()
        request.user = user2
        view = Mock()

        permission = IsAssigner()
        assert permission.has_object_permission(request, view, task) is True


@pytest.mark.django_db
class TestIsTaskItemExecutorOrAssigner:
    """Tests for IsTaskItemExecutorOrAssigner permission."""

    def test_assigner_has_permission(self, task_item, user):
        """Test that task assigner has permission to modify task item."""
        request = Mock()
        request.user = user
        request.method = 'PATCH'
        request.data = {'status': 'in_progress'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is True

    def test_executor_can_update_status(self, task_item, user2):
        """Test that executor can update only status."""
        request = Mock()
        request.user = user2
        request.method = 'PATCH'
        request.data = {'status': 'in_progress'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is True

    def test_executor_cannot_update_other_fields(self, task_item, user2):
        """Test that executor cannot update fields other than status."""
        request = Mock()
        request.user = user2
        request.method = 'PATCH'
        request.data = {'title': 'New Title', 'status': 'in_progress'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is False

    def test_non_participant_no_permission(self, task_item, user3):
        """Test that non-participant has no permission."""
        request = Mock()
        request.user = user3
        request.method = 'PATCH'
        request.data = {'status': 'in_progress'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is False

    def test_staff_user_has_permission(self, task_item, user3):
        """Test that staff user always has permission."""
        user3.is_staff = True
        user3.save()

        request = Mock()
        request.user = user3
        request.method = 'PATCH'
        request.data = {'title': 'New Title'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is True

    def test_executor_can_only_patch_status(self, task_item, user2):
        """Test executor can only update status field."""
        # Test with only status
        request = Mock()
        request.user = user2
        request.method = 'PATCH'
        request.data = {'status': 'completed'}
        view = Mock()

        permission = IsTaskItemExecutorOrAssigner()
        assert permission.has_object_permission(request, view, task_item) is True

        # Test with status + other fields
        request.data = {'status': 'completed', 'planned_hours': 10}
        assert permission.has_object_permission(request, view, task_item) is False
