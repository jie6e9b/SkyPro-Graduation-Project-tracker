"""Pytest fixtures for tasks app tests."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.tasks.models import Task, TaskRole, TaskItem

User = get_user_model()


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='User',
        position='Engineer',
        department='IT'
    )


@pytest.fixture
def user2(db):
    """Create and return a second test user."""
    return User.objects.create_user(
        email='test2@example.com',
        password='TestPass123!',
        first_name='John',
        last_name='Doe',
        position='Engineer',
        department='IT'
    )


@pytest.fixture
def user3(db):
    """Create and return a third test user."""
    return User.objects.create_user(
        email='test3@example.com',
        password='TestPass123!',
        first_name='Jane',
        last_name='Smith',
        position='Manager',
        department='Management'
    )


@pytest.fixture
def task(db, user):
    """Create and return a test task with assigner role."""
    task = Task.objects.create(
        title='Test Task',
        description='Test Description',
        status='new',
        planned_start_date='2025-11-01',
        planned_end_date='2025-11-30'
    )

    # Create assigner role
    TaskRole.objects.create(
        task=task,
        user=user,
        role='assigner'
    )

    return task


@pytest.fixture
def task_with_items(db, task, user2, user3):
    """Create a task with multiple task items."""
    # Add co-executor
    TaskRole.objects.create(
        task=task,
        user=user2,
        role='co_executor'
    )

    # Add observer
    TaskRole.objects.create(
        task=task,
        user=user3,
        role='observer'
    )

    # Add task items
    TaskItem.objects.create(
        task=task,
        title='Task Item 1',
        description='Description 1',
        executor=user2,
        status='todo',
        planned_hours=8,
        order=0
    )

    TaskItem.objects.create(
        task=task,
        title='Task Item 2',
        description='Description 2',
        executor=user2,
        status='in_progress',
        planned_hours=16,
        order=1
    )

    TaskItem.objects.create(
        task=task,
        title='Task Item 3',
        description='Description 3',
        executor=user3,
        status='completed',
        planned_hours=4,
        order=2
    )

    return task


@pytest.fixture
def task_item(db, task, user2):
    """Create and return a test task item."""
    return TaskItem.objects.create(
        task=task,
        title='Test Task Item',
        description='Test Description',
        executor=user2,
        status='todo',
        planned_hours=8,
        order=0
    )
