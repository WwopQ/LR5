import logging

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class PromoCode(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Промокод',
        help_text='Например: SUMMER2026',
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Скидка, %',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        db_index=True,
    )
    valid_from = models.DateField(verbose_name='Действует с')
    valid_to = models.DateField(verbose_name='Действует до')

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-valid_to']

    def __str__(self):
        return f'{self.code} ({self.discount_pct}%)'

    @property
    def is_currently_valid(self):
        """True если промокод активен и попадает в даты действия."""
        today = timezone.now().date()
        return self.is_active and self.valid_from <= today <= self.valid_to
