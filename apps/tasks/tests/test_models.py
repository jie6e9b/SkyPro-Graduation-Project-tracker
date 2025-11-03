"""Tests for tasks app models."""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.tasks.models import Task, TaskRole, TaskItem


@pytest.mark.django_db
class TestTaskModel:
    """Tests for Task model."""

    def test_task_creation(self, user):
        """Test creating a task."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            status='new'
        )

        assert task.title == 'Test Task'
        assert task.description == 'Test Description'
        assert task.status == 'new'
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_str_representation(self, task):
        """Test task string representation."""
        assert str(task) == 'Test Task'

    def test_task_progress_percentage_no_items(self, task):
        """Test progress calculation with no items."""
        assert task.progress_percentage == 0

    def test_task_progress_percentage_with_items(self, task_with_items):
        """Test progress calculation with items."""
        # task_with_items has 3 items: todo, in_progress, completed
        # Only 1 is completed, so progress should be 33.33%
        assert task_with_items.progress_percentage == 33.33

    def test_task_total_planned_hours(self, task_with_items):
        """Test total planned hours calculation."""
        # Items have 8 + 16 + 4 = 28 planned hours
        assert task_with_items.total_planned_hours == 28

    def test_task_assigner_property(self, task, user):
        """Test getting task assigner."""
        assert task.assigner == user

    def test_task_get_participants(self, task_with_items, user, user2, user3):
        """Test getting all task participants."""
        participants = task_with_items.get_participants()
        assert user in participants  # assigner
        assert user2 in participants  # co_executor
        assert user3 in participants  # observer

    def test_task_source_links_default(self, task):
        """Test source_links default value."""
        assert task.source_links == []

    def test_task_source_links_with_data(self, user):
        """Test source_links with data."""
        task = Task.objects.create(
            title='Test',
            description='Test',
            source_links=['https://example.com', 'https://test.com']
        )
        assert len(task.source_links) == 2
        assert 'https://example.com' in task.source_links


@pytest.mark.django_db
class TestTaskRoleModel:
    """Tests for TaskRole model."""

    def test_task_role_creation(self, task, user2):
        """Test creating a task role."""
        role = TaskRole.objects.create(
            task=task,
            user=user2,
            role='co_executor'
        )

        assert role.task == task
        assert role.user == user2
        assert role.role == 'co_executor'
        assert role.assigned_at is not None

    def test_task_role_str_representation(self, task, user2):
        """Test task role string representation."""
        role = TaskRole.objects.create(
            task=task,
            user=user2,
            role='co_executor'
        )
        expected = f"{user2.get_full_name()} - Соисполнитель в {task.title}"
        assert str(role) == expected

    def test_only_one_assigner_per_task(self, task, user, user2):
        """Test that only one assigner can exist per task."""
        # task already has user as assigner (from fixture)
        role = TaskRole(
            task=task,
            user=user2,
            role='assigner'
        )

        with pytest.raises(ValidationError) as exc_info:
            role.clean()

        assert 'У задачи уже есть постановщик' in str(exc_info.value)

    def test_multiple_co_executors_allowed(self, task, user2, user3):
        """Test that multiple co-executors are allowed."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')
        TaskRole.objects.create(task=task, user=user3, role='co_executor')

        co_executors = TaskRole.objects.filter(task=task, role='co_executor')
        assert co_executors.count() == 2

    def test_multiple_observers_allowed(self, task, user2, user3):
        """Test that multiple observers are allowed."""
        TaskRole.objects.create(task=task, user=user2, role='observer')
        TaskRole.objects.create(task=task, user=user3, role='observer')

        observers = TaskRole.objects.filter(task=task, role='observer')
        assert observers.count() == 2

    def test_unique_together_constraint(self, task, user2):
        """Test unique_together constraint for (task, user, role)."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')

        # Try to create the same role again
        with pytest.raises(Exception):  # IntegrityError
            TaskRole.objects.create(task=task, user=user2, role='co_executor')


@pytest.mark.django_db
class TestTaskItemModel:
    """Tests for TaskItem model."""

    def test_task_item_creation(self, task, user2):
        """Test creating a task item."""
        item = TaskItem.objects.create(
            task=task,
            title='Test Item',
            description='Test Description',
            executor=user2,
            status='todo',
            planned_hours=8
        )

        assert item.task == task
        assert item.title == 'Test Item'
        assert item.description == 'Test Description'
        assert item.executor == user2
        assert item.status == 'todo'
        assert item.planned_hours == 8
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_task_item_str_representation(self, task_item):
        """Test task item string representation."""
        expected = f"{task_item.task.title} - {task_item.title}"
        assert str(task_item) == expected

    def test_task_item_without_executor(self, task):
        """Test creating task item without executor."""
        item = TaskItem.objects.create(
            task=task,
            title='Unassigned Item',
            status='todo'
        )

        assert item.executor is None

    def test_task_item_default_status(self, task):
        """Test task item default status."""
        item = TaskItem.objects.create(
            task=task,
            title='New Item'
        )

        assert item.status == 'todo'

    def test_task_item_default_planned_hours(self, task):
        """Test task item default planned hours."""
        item = TaskItem.objects.create(
            task=task,
            title='New Item'
        )

        assert item.planned_hours == 0

    def test_task_item_completed_at_auto_set(self, task_item):
        """Test that completed_at is set automatically when status changes to completed."""
        assert task_item.completed_at is None

        task_item.status = 'completed'
        task_item.save()
        task_item.refresh_from_db()

        assert task_item.completed_at is not None

    def test_task_item_completed_at_cleared_on_status_change(self, task, user2):
        """Test that completed_at is cleared when status changes from completed."""
        item = TaskItem.objects.create(
            task=task,
            title='Test Item',
            executor=user2,
            status='completed'
        )

        assert item.completed_at is not None

        item.status = 'in_progress'
        item.save()
        item.refresh_from_db()

        assert item.completed_at is None

    def test_task_item_ordering(self, task, user2):
        """Test task items are ordered by order field."""
        item1 = TaskItem.objects.create(task=task, title='Item 1', order=2, executor=user2)
        item2 = TaskItem.objects.create(task=task, title='Item 2', order=0, executor=user2)
        item3 = TaskItem.objects.create(task=task, title='Item 3', order=1, executor=user2)

        items = list(task.items.all())
        assert items[0] == item2  # order=0
        assert items[1] == item3  # order=1
        assert items[2] == item1  # order=2

    def test_task_item_cascade_delete(self, task, task_item):
        """Test that task items are deleted when task is deleted."""
        task_id = task.id
        item_id = task_item.id

        task.delete()

        assert not Task.objects.filter(id=task_id).exists()
        assert not TaskItem.objects.filter(id=item_id).exists()
