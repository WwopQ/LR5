import logging

from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


class CompanyInfo(models.Model):
    """
    Информация о компании (страница «О компании»).
    Синглтон — в базе должна быть ровно одна запись.
    """
    text = models.TextField(verbose_name='Основной текст')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    logo = models.ImageField(
        upload_to='company/', blank=True, null=True, verbose_name='Логотип'
    )
    requisites = models.TextField(blank=True, verbose_name='Реквизиты')

    class Meta:
        verbose_name = 'Информация о компании'
        verbose_name_plural = 'Информация о компании'

    def __str__(self):
        return 'О компании'

    def clean(self):
        """Не даём создать вторую запись."""
        if not self.pk and CompanyInfo.objects.exists():
            raise ValidationError(
                'Может существовать только одна запись «Информация о компании».'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        logger.info('CompanyInfo сохранена (pk=%s)', self.pk)
        super().save(*args, **kwargs)


class CompanyHistory(models.Model):
    """
    История компании по годам (отображается на странице «О компании»).
    """
    company_info = models.ForeignKey(
        CompanyInfo,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Компания',
    )
    year = models.PositiveSmallIntegerField(verbose_name='Год')
    description = models.TextField(verbose_name='Описание события')

    class Meta:
        verbose_name = 'Запись истории'
        verbose_name_plural = 'История компании'
        ordering = ['year']

    def __str__(self):
        return f'{self.year}: {self.description[:50]}'


class Employee(models.Model):
    """
    Сотрудник компании (страница «Контакты»).
    """
    photo = models.ImageField(
        upload_to='employees/', blank=True, null=True, verbose_name='Фото'
    )
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    position = models.CharField(max_length=200, verbose_name='Должность')
    description = models.TextField(blank=True, verbose_name='Описание работ')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок отображения',
        help_text='Меньшее число — выше в списке',
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['order', 'last_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} — {self.position}'

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)
