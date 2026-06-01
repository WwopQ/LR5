import logging
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r'^\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}$')


def validate_phone(value):
    """Формат: +375 (29) XXX-XX-XX"""
    if not PHONE_REGEX.match(value):
        raise ValidationError(
            'Введите номер в формате +375 (29) XXX-XX-XX. '
            'Допустимые коды: 29, 33, 44, 25.'
        )


def validate_age(value):
    """Клиент должен быть старше 18 лет."""
    today = timezone.now().date()
    age = (today - value).days // 365
    if age < 18:
        raise ValidationError(
            f'Возраст должен быть не менее 18 лет. Ваш возраст: {age} лет.'
        )


class Profile(models.Model):
    """
    Расширенный профиль пользователя (OneToOne → User).
    Создаётся автоматически при регистрации.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone],
        verbose_name='Телефон',
        help_text='Формат: +375 (29) XXX-XX-XX',
    )
    birth_date = models.DateField(
        validators=[validate_age],
        verbose_name='Дата рождения',
        help_text='Только для лиц старше 18 лет',
    )
    address = models.CharField(max_length=300, blank=True, verbose_name='Адрес')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль: {self.user.get_full_name() or self.user.username}'

    @property
    def age(self):
        today = timezone.now().date()
        return (today - self.birth_date).days // 365
