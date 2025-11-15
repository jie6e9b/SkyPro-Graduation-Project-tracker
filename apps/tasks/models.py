"""Models for tasks app."""
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class Task(models.Model):
    """
    Main task model.
    
    Represents a high-level task that can be decomposed into subtasks (TaskItems).
    """
    
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('review', 'На проверке'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание')
    source_links = models.JSONField('Ссылки на исходные данные', default=list, blank=True)
    result_link = models.URLField('Ссылка на результат', blank=True, null=True)
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    
    planned_start_date = models.DateField('Плановая дата начала', null=True, blank=True)
    actual_start_date = models.DateField('Фактическая дата начала', null=True, blank=True)
    planned_end_date = models.DateField('Плановая дата окончания', null=True, blank=True)
    actual_end_date = models.DateField('Фактическая дата окончания', null=True, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_end_date']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        """Calculate task progress based on completed subtasks."""
        items = self.items.all()
        if not items:
            return 0
        completed = items.filter(status='completed').count()
        return round((completed / items.count()) * 100, 2)
    
    @property
    def total_planned_hours(self):
        """Sum of planned hours from all subtasks."""
        return self.items.aggregate(
            total=models.Sum('planned_hours')
        )['total'] or 0
    
    @property
    def total_spent_hours(self):
        """Sum of spent hours from all time logs."""
        try:
            from apps.timelogs.models import TimeLog
            return TimeLog.objects.filter(task=self).aggregate(
                total=models.Sum('hours')
            )['total'] or 0
        except ImportError:
            # TimeLog model doesn't exist yet
            return 0
    
    @property
    def assigner(self):
        """Get the task assigner (creator)."""
        role = self.roles.filter(role='assigner').first()
        return role.user if role else None
    
    def get_participants(self):
        """Get all task participants (all roles)."""
        User = get_user_model()
        return User.objects.filter(
            task_roles__task=self
        ).distinct()


class TaskRole(models.Model):
    """
    Task participant roles.
    
    Defines who has access to the task and what permissions they have.
    """
    
    ROLE_CHOICES = [
        ('assigner', 'Постановщик'),
        ('co_executor', 'Соисполнитель'),
        ('observer', 'Наблюдатель'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='roles', verbose_name='Задача')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_roles',
        verbose_name='Пользователь'
    )
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField('Дата назначения', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Роль в задаче'
        verbose_name_plural = 'Роли в задачах'
        unique_together = ('task', 'user', 'role')
        indexes = [
            models.Index(fields=['task', 'user']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} в {self.task.title}"
    
    def clean(self):
        """Validate that there can be only one assigner per task."""
        if self.role == 'assigner':
            existing_assigner = TaskRole.objects.filter(
                task=self.task,
                role='assigner'
            ).exclude(pk=self.pk).exists()
            
            if existing_assigner:
                raise ValidationError('У задачи уже есть постановщик')


class TaskItem(models.Model):
    """
    Task item (subtask).
    
    Represents a decomposed part of the main task with specific executor.
    """
    
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('blocked', 'Заблокирована'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='items', verbose_name='Задача')
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_items',
        verbose_name='Исполнитель'
    )
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='todo')
    planned_hours = models.DecimalField(
        'Плановая трудоемкость (часы)',
        max_digits=6,
        decimal_places=2,
        default=0
    )
    order = models.PositiveIntegerField('Порядок', default=0)
    
    completed_at = models.DateTimeField('Дата завершения', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Подзадача'
        verbose_name_plural = 'Подзадачи'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['task', 'status']),
            models.Index(fields=['executor']),
        ]
    
    def __str__(self):
        return f"{self.task.title} - {self.title}"
    
    @property
    def spent_hours(self):
        """Sum of spent hours from time logs for this item."""
        try:
            from apps.timelogs.models import TimeLog
            return TimeLog.objects.filter(task_item=self).aggregate(
                total=models.Sum('hours')
            )['total'] or 0
        except ImportError:
            # TimeLog model doesn't exist yet
            return 0
    
    def save(self, *args, **kwargs):
        """Auto-set completed_at when status changes to completed."""
        from django.utils import timezone
        
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed' and self.completed_at:
            self.completed_at = None
        
        super().save(*args, **kwargs)
