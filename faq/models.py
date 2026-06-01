import logging

from django.db import models

logger = logging.getLogger(__name__)


class FAQ(models.Model):
    question = models.CharField(max_length=500, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')
    date_added = models.DateField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Вопрос и ответ'
        verbose_name_plural = 'Вопросы и ответы'
        ordering = ['-date_added', '-pk']  # pk — tiebreaker внутри одной даты

    def __str__(self):
        return self.question[:80]
