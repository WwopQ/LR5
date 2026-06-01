import logging

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Article(models.Model):
    """Новостная статья."""

    title = models.CharField(max_length=250, verbose_name='Заголовок')
    summary = models.CharField(
        max_length=500,
        verbose_name='Краткое содержание',
        help_text='Одно предложение — отображается в списке новостей и на главной',
    )
    content = models.TextField(verbose_name='Полный текст')
    image = models.ImageField(
        upload_to='news/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Картинка',
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Опубликовано',
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации',
        help_text='Заполняется автоматически при первой публикации',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Автоматически проставляем дату публикации при первой публикации
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
            logger.info('Статья "%s" опубликована: %s', self.title, self.published_at)
        super().save(*args, **kwargs)
