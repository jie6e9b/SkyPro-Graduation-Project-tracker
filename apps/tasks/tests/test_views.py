"""Tests for tasks app views."""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.tasks.models import Task, TaskRole, TaskItem


@pytest.mark.django_db
class TestTaskViewSet:
    """Tests for TaskViewSet."""

    def test_list_tasks_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list tasks."""
        url = reverse('task-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tasks_authenticated(self, api_client, user, task):
        """Test that authenticated users can list their tasks."""
        api_client.force_authenticate(user=user)
        url = reverse('task-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Test Task'

    def test_list_tasks_only_show_user_tasks(self, api_client, user, user2, task):
        """Test that users only see tasks they participate in."""
        # Create another task for user2
        other_task = Task.objects.create(
            title='Other Task',
            description='Other Description'
        )
        TaskRole.objects.create(task=other_task, user=user2, role='assigner')

        # Authenticate as user
        api_client.force_authenticate(user=user)
        url = reverse('task-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == task.id

    def test_create_task(self, api_client, user):
        """Test creating a new task."""
        api_client.force_authenticate(user=user)
        url = reverse('task-list')
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'planned_start_date': '2025-11-01',
            'planned_end_date': '2025-11-30'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.count() == 1
        task = Task.objects.first()
        assert task.title == 'New Task'
        assert task.assigner == user

    def test_create_task_with_items_and_roles(self, api_client, user, user2, user3):
        """Test creating a task with items and roles."""
        api_client.force_authenticate(user=user)
        url = reverse('task-list')
        data = {
            'title': 'Complex Task',
            'description': 'Complex Description',
            'co_executors': [user2.id],
            'observers': [user3.id],
            'task_items': [
                {
                    'title': 'Item 1',
                    'description': 'Desc 1',
                    'executor_id': user2.id,
                    'planned_hours': 8
                },
                {
                    'title': 'Item 2',
                    'executor_id': user3.id,
                    'planned_hours': 16
                }
            ]
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        task = Task.objects.first()
        assert task.roles.count() == 3  # assigner, co_executor, observer
        assert task.items.count() == 2

    def test_retrieve_task(self, api_client, user, task):
        """Test retrieving task details."""
        api_client.force_authenticate(user=user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Task'
        assert 'roles' in response.data
        assert 'items' in response.data

    def test_retrieve_task_non_participant(self, api_client, user2, task):
        """Test that non-participants cannot retrieve task."""
        api_client.force_authenticate(user=user2)
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_as_assigner(self, api_client, user, task):
        """Test updating task as assigner."""
        api_client.force_authenticate(user=user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {
            'title': 'Updated Task',
            'status': 'in_progress'
        }
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Updated Task'
        assert task.status == 'in_progress'

    def test_update_task_non_assigner(self, api_client, user2, task):
        """Test that non-assigners cannot update task."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')

        api_client.force_authenticate(user=user2)
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {'title': 'Hacked'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_task_as_assigner(self, api_client, user, task):
        """Test deleting task as assigner."""
        api_client.force_authenticate(user=user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Task.objects.count() == 0

    def test_delete_task_non_assigner(self, api_client, user2, task):
        """Test that non-assigners cannot delete task."""
        TaskRole.objects.create(task=task, user=user2, role='co_executor')

        api_client.force_authenticate(user=user2)
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_my_tasks_endpoint(self, api_client, user, user2, task):
        """Test /tasks/my/ endpoint returns tasks where user participates."""
        # Create another task where user is co-executor
        other_task = Task.objects.create(title='Other', description='Desc')
        TaskRole.objects.create(task=other_task, user=user2, role='assigner')
        TaskRole.objects.create(task=other_task, user=user, role='co_executor')

        api_client.force_authenticate(user=user)
        url = reverse('task-my')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_my_items_endpoint(self, api_client, user2, task):
        """Test /tasks/my_items/ endpoint returns items where user is executor."""
        TaskItem.objects.create(task=task, title='Item 1', executor=user2, planned_hours=8)
        TaskItem.objects.create(task=task, title='Item 2', executor=user2, planned_hours=4)

        api_client.force_authenticate(user=user2)
        url = reverse('task-my-items')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_assigned_by_me_endpoint(self, api_client, user, user2):
        """Test /tasks/assigned_by_me/ endpoint returns tasks created by user."""
        # Create tasks assigned by user
        task1 = Task.objects.create(title='Task 1', description='Desc 1')
        TaskRole.objects.create(task=task1, user=user, role='assigner')

        task2 = Task.objects.create(title='Task 2', description='Desc 2')
        TaskRole.objects.create(task=task2, user=user, role='assigner')

        # Create task assigned by user2
        task3 = Task.objects.create(title='Task 3', description='Desc 3')
        TaskRole.objects.create(task=task3, user=user2, role='assigner')

        api_client.force_authenticate(user=user)
        url = reverse('task-assigned-by-me')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_add_role_endpoint(self, api_client, user, user2, task):
        """Test adding role to task."""
        api_client.force_authenticate(user=user)
        url = reverse('task-add-role', kwargs={'pk': task.id})
        data = {
            'user_id': user2.id,
            'role': 'co_executor'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert TaskRole.objects.filter(task=task, user=user2, role='co_executor').exists()

    def test_remove_role_endpoint(self, api_client, user, user2, task):
        """Test removing role from task."""
        role = TaskRole.objects.create(task=task, user=user2, role='co_executor')

        api_client.force_authenticate(user=user)
        url = reverse('task-remove-role', kwargs={'pk': task.id, 'role_id': role.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TaskRole.objects.filter(id=role.id).exists()

    def test_cannot_remove_assigner_role(self, api_client, user, task):
        """Test that assigner role cannot be removed."""
        assigner_role = TaskRole.objects.get(task=task, user=user, role='assigner')

        api_client.force_authenticate(user=user)
        url = reverse('task-remove-role', kwargs={'pk': task.id, 'role_id': assigner_role.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert TaskRole.objects.filter(id=assigner_role.id).exists()

    def test_add_item_endpoint(self, api_client, user, user2, task):
        """Test adding task item to task."""
        api_client.force_authenticate(user=user)
        url = reverse('task-add-item', kwargs={'pk': task.id})
        data = {
            'title': 'New Item',
            'description': 'New Description',
            'executor_id': user2.id,
            'planned_hours': 16
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert TaskItem.objects.filter(task=task, title='New Item').exists()


@pytest.mark.django_db
class TestTaskItemViewSet:
    """Tests for TaskItemViewSet."""

    def test_list_task_items_authenticated(self, api_client, user, task_item):
        """Test listing task items."""
        api_client.force_authenticate(user=user)
        url = reverse('taskitem-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_retrieve_task_item(self, api_client, user, task_item):
        """Test retrieving task item."""
        api_client.force_authenticate(user=user)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Task Item'

    def test_update_task_item_as_assigner(self, api_client, user, task_item):
        """Test updating task item as assigner."""
        api_client.force_authenticate(user=user)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        data = {
            'title': 'Updated Item',
            'status': 'in_progress'
        }
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        task_item.refresh_from_db()
        assert task_item.title == 'Updated Item'
        assert task_item.status == 'in_progress'

    def test_update_task_item_status_as_executor(self, api_client, user2, task_item):
        """Test executor can update status."""
        api_client.force_authenticate(user=user2)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        data = {'status': 'completed'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        task_item.refresh_from_db()
        assert task_item.status == 'completed'

    def test_executor_cannot_update_other_fields(self, api_client, user2, task_item):
        """Test executor cannot update fields other than status."""
        api_client.force_authenticate(user=user2)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        data = {
            'title': 'Hacked',
            'status': 'in_progress'
        }
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_task_item_as_assigner(self, api_client, user, task_item):
        """Test deleting task item as assigner."""
        api_client.force_authenticate(user=user)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TaskItem.objects.filter(id=task_item.id).exists()

    def test_executor_cannot_delete_task_item(self, api_client, user2, task_item):
        """Test that executor cannot delete task item."""
        api_client.force_authenticate(user=user2)
        url = reverse('taskitem-detail', kwargs={'pk': task_item.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskFiltering:
    """Tests for task filtering."""

    def test_filter_by_status(self, api_client, user):
        """Test filtering tasks by status."""
        task1 = Task.objects.create(title='Task 1', description='Desc', status='new')
        TaskRole.objects.create(task=task1, user=user, role='assigner')

        task2 = Task.objects.create(title='Task 2', description='Desc', status='in_progress')
        TaskRole.objects.create(task=task2, user=user, role='assigner')

        api_client.force_authenticate(user=user)
        url = reverse('task-list') + '?status=new'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'new'

    def test_filter_by_assigner(self, api_client, user, user2):
        """Test filtering tasks by assigner."""
        task1 = Task.objects.create(title='Task 1', description='Desc')
        TaskRole.objects.create(task=task1, user=user, role='assigner')

        task2 = Task.objects.create(title='Task 2', description='Desc')
        TaskRole.objects.create(task=task2, user=user2, role='assigner')
        TaskRole.objects.create(task=task2, user=user, role='co_executor')

        api_client.force_authenticate(user=user)
        url = reverse('task-list') + f'?assigner={user.id}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['assigner']['id'] == user.id

    def test_filter_by_executor(self, api_client, user, user2, task):
        """Test filtering tasks by executor."""
        TaskItem.objects.create(task=task, title='Item 1', executor=user2)

        api_client.force_authenticate(user=user)
        url = reverse('task-list') + f'?executor={user2.id}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_task_items_by_status(self, api_client, user, task):
        """Test filtering task items by status."""
        TaskItem.objects.create(task=task, title='Item 1', executor=user, status='todo')
        TaskItem.objects.create(task=task, title='Item 2', executor=user, status='completed')

        api_client.force_authenticate(user=user)
        url = reverse('taskitem-list') + '?status=todo'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'todo'


@pytest.mark.django_db
class TestTaskValidation:
    """Tests for task validation."""

    def test_cannot_complete_task_with_incomplete_items(self, api_client, user, task_with_items):
        """Test that task cannot be completed if items are not completed."""
        api_client.force_authenticate(user=user)
        url = reverse('task-detail', kwargs={'pk': task_with_items.id})
        data = {'status': 'completed'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Невозможно завершить задачу' in str(response.data)
