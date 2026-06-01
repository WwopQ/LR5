import logging

from django.db import models

logger = logging.getLogger(__name__)


class Vacancy(models.Model):
    title = models.CharField(max_length=250, verbose_name='Название вакансии')
    description = models.TextField(verbose_name='Описание')
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
        db_index=True,
        help_text='Снимите флажок, чтобы перенести вакансию в архив',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        status = 'активна' if self.is_active else 'архив'
        return f'{self.title} [{status}]'
