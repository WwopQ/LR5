import logging
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

PHONE_REGEX = re.compile(r'^\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}$')


def validate_phone(value):
    if not PHONE_REGEX.match(value):
        raise ValidationError(
            'Введите номер в формате +375 (29) XXX-XX-XX. Коды: 29, 33, 44, 25.'
        )


def validate_age(value):
    today = timezone.now().date()
    age = (today - value).days // 365
    if age < 18:
        raise ValidationError(f'Возраст должен быть не менее 18 лет. Ваш: {age}.')


# ─── Справочники ─────────────────────────────────────────────────────────────

class BodyType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Тип кузова')

    class Meta:
        verbose_name = 'Тип кузова'
        verbose_name_plural = 'Типы кузова'
        ordering = ['name']

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.CharField(max_length=100, verbose_name='Марка')
    model_name = models.CharField(max_length=100, verbose_name='Модель')
    body_type = models.ForeignKey(
        BodyType,
        on_delete=models.PROTECT,
        related_name='car_models',
        verbose_name='Тип кузова',
    )

    class Meta:
        verbose_name = 'Модель автомобиля'
        verbose_name_plural = 'Модели автомобилей'
        ordering = ['brand', 'model_name']
        unique_together = ('brand', 'model_name')

    def __str__(self):
        return f'{self.brand} {self.model_name}'


class CarPark(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название парка')
    address = models.CharField(max_length=300, verbose_name='Адрес')

    class Meta:
        verbose_name = 'Автопарк'
        verbose_name_plural = 'Автопарки'
        ordering = ['name']

    def __str__(self):
        return self.name


class Discount(models.Model):
    name = models.CharField(max_length=200, verbose_name='Наименование скидки')
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Процент скидки',
    )

    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.percentage}%)'


class Fine(models.Model):
    name = models.CharField(max_length=200, verbose_name='Наименование штрафа')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Сумма штрафа (руб.)',
    )

    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.amount} руб.)'


# ─── Основные сущности ────────────────────────────────────────────────────────

class Car(models.Model):
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Государственный номер',
    )
    car_model = models.ForeignKey(
        CarModel,
        on_delete=models.PROTECT,
        related_name='cars',
        verbose_name='Модель',
    )
    car_park = models.ForeignKey(
        CarPark,
        on_delete=models.PROTECT,
        related_name='cars',
        verbose_name='Автопарк',
    )
    year = models.PositiveSmallIntegerField(
        verbose_name='Год выпуска',
        validators=[MinValueValidator(1990), MaxValueValidator(2030)],
    )
    car_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Стоимость автомобиля (руб.)',
    )
    daily_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Суточная стоимость проката (руб.)',
    )

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['car_model__brand', 'car_model__model_name']

    def __str__(self):
        return f'{self.car_model} ({self.license_plate}, {self.year})'


class Client(models.Model):
    """
    Профиль клиента пункта проката (OneToOne → User).
    Отличается от users.Profile: содержит только поля,
    специфичные для предметной области «Прокат автомобилей».
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Аккаунт',
    )
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    address = models.CharField(max_length=300, verbose_name='Адрес')
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone],
        verbose_name='Телефон',
        help_text='+375 (29) XXX-XX-XX',
    )
    birth_date = models.DateField(
        validators=[validate_age],
        verbose_name='Дата рождения',
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)

    @property
    def age(self):
        today = timezone.now().date()
        return (today - self.birth_date).days // 365


# ─── Прокат ───────────────────────────────────────────────────────────────────

class Rental(models.Model):
    car = models.ForeignKey(
        Car,
        on_delete=models.PROTECT,
        related_name='rentals',
        verbose_name='Автомобиль',
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='rentals',
        verbose_name='Клиент',
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rentals',
        verbose_name='Скидка',
    )
    # ManyToMany: у одного проката может быть несколько штрафов
    fines = models.ManyToManyField(
        Fine,
        blank=True,
        related_name='rentals',
        verbose_name='Штрафы',
    )

    issue_date = models.DateField(verbose_name='Дата выдачи')
    days_count = models.PositiveIntegerField(
        verbose_name='Количество дней',
        validators=[MinValueValidator(1)],
    )
    expected_return_date = models.DateField(
        verbose_name='Ожидаемая дата возврата',
        editable=False,
    )

    # Финансовые поля — рассчитываются в save()
    rental_sum = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Сумма проката (руб.)',
        help_text='Суточная цена × количество дней',
    )
    discount_sum = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки (руб.)',
    )
    fine_sum = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Сумма штрафов (руб.)',
    )
    total_sum = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Итоговая сумма (руб.)',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Прокат'
        verbose_name_plural = 'Прокаты'
        ordering = ['-issue_date']

    def __str__(self):
        return f'Прокат #{self.pk}: {self.car} — {self.client}'

    def calculate_sums(self):
        """
        Пересчитывает финансовые поля:
          rental_sum  = daily_price * days_count
          discount_sum = rental_sum * percentage / 100
          fine_sum    = сумма всех штрафов (из ManyToMany, после save)
          total_sum   = rental_sum - discount_sum + fine_sum
        Вызывается в save() и после изменения fines через m2m_changed.
        """
        from decimal import Decimal
        self.rental_sum = self.car.daily_price * self.days_count

        if self.discount:
            self.discount_sum = (self.rental_sum * self.discount.percentage / Decimal('100'))
        else:
            self.discount_sum = Decimal('0')

        # fine_sum пересчитывается отдельно в recalculate_fines() после m2m_changed
        self.total_sum = self.rental_sum - self.discount_sum + self.fine_sum

    def recalculate_fines(self):
        """Вызывается после изменения ManyToMany fines."""
        from decimal import Decimal
        self.fine_sum = self.fines.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        self.total_sum = self.rental_sum - self.discount_sum + self.fine_sum
        self.save(update_fields=['fine_sum', 'total_sum'])

    def save(self, *args, **kwargs):
        from datetime import timedelta
        self.expected_return_date = self.issue_date + timedelta(days=self.days_count)
        self.calculate_sums()
        logger.info(
            'Rental save: car=%s, client=%s, total=%s',
            self.car_id, self.client_id, self.total_sum,
        )
        super().save(*args, **kwargs)


def rental_fines_changed(sender, instance, action, **kwargs):
    """Пересчитываем сумму штрафов при изменении M2M."""
    if action in ('post_add', 'post_remove', 'post_clear'):
        instance.recalculate_fines()


models.signals.m2m_changed.connect(rental_fines_changed, sender=Rental.fines.through)
