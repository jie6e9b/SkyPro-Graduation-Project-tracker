"""Models for timelogs app."""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class TimeLog(models.Model):
    """
    Time log entry for tracking work hours.

    Records time spent on tasks and task items by users.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='timelogs',
        verbose_name='Пользователь'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='timelogs',
        verbose_name='Задача'
    )
    task_item = models.ForeignKey(
        'tasks.TaskItem',
        on_delete=models.CASCADE,
        related_name='timelogs',
        null=True,
        blank=True,
        verbose_name='Подзадача'
    )

    date = models.DateField('Дата работы')
    hours = models.DecimalField(
        'Часы',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.TextField('Описание работы')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Запись времени'
        verbose_name_plural = 'Записи времени'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['task', '-date']),
            models.Index(fields=['task_item', '-date']),
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.task.title} - {self.hours}ч ({self.date})"

    def clean(self):
        """Validate that task_item belongs to task if provided."""
        super().clean()

        if self.task_item and self.task_item.task_id != self.task_id:
            raise ValidationError({
                'task_item': 'Подзадача должна принадлежать указанной задаче'
            })

    def save(self, *args, **kwargs):
        """Run full_clean before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
