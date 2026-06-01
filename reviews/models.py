import logging

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

logger = logging.getLogger(__name__)

RATING_CHOICES = [
    (1, '1 — Очень плохо'),
    (2, '2 — Плохо'),
    (3, '3 — Нормально'),
    (4, '4 — Хорошо'),
    (5, '5 — Отлично'),
]


class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name='Пользователь',
    )
    # Имя сохраняется всегда: берётся из профиля при входе или вводится вручную
    name = models.CharField(max_length=150, verbose_name='Имя')
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка',
    )
    text = models.TextField(verbose_name='Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Одобрен',
        db_index=True,
        help_text='Только одобренные отзывы видны на сайте',
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.rating}/5'
