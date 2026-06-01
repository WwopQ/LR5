"""
Сервисный слой: внешние API + расчёт статистики.
"""
import logging
import statistics
from decimal import Decimal

import requests
from django.db.models import Avg, Sum, Count, Max, Min

logger = logging.getLogger(__name__)

# ─── Внешние API ─────────────────────────────────────────────────────────────

RANDOM_USER_URL = 'https://randomuser.me/api/'
EXCHANGE_RATES_URL = 'https://api.exchangerate-api.com/v4/latest/BYN'


def fetch_random_user():
    """
    API 1: RandomUser — возвращает случайного пользователя.
    Используется для демонстрации данных на странице статистики.
    Документация: https://randomuser.me/
    """
    try:
        response = requests.get(RANDOM_USER_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        user = data['results'][0]
        return {
            'name': f"{user['name']['first']} {user['name']['last']}",
            'email': user['email'],
            'country': user['location']['country'],
            'picture': user['picture']['thumbnail'],
        }
    except requests.RequestException as e:
        logger.error('RandomUser API недоступен: %s', e)
        return None
    except (KeyError, IndexError) as e:
        logger.error('RandomUser API: неожиданный формат ответа: %s', e)
        return None


def fetch_exchange_rates():
    """
    API 2: ExchangeRate-API — курсы валют относительно BYN.
    Используется для отображения стоимости проката в других валютах.
    Документация: https://www.exchangerate-api.com/
    """
    try:
        response = requests.get(EXCHANGE_RATES_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        rates = data.get('rates', {})
        # Возвращаем только нужные валюты
        return {
            'USD': round(rates.get('USD', 0), 4),
            'EUR': round(rates.get('EUR', 0), 4),
            'RUB': round(rates.get('RUB', 0), 4),
        }
    except requests.RequestException as e:
        logger.error('ExchangeRate API недоступен: %s', e)
        return None
    except (KeyError, ValueError) as e:
        logger.error('ExchangeRate API: неожиданный формат ответа: %s', e)
        return None


# ─── Расчёт статистики ───────────────────────────────────────────────────────

def get_rental_statistics():
    """
    Возвращает статистику по прокатам:
    - Общие показатели
    - Среднее, медиана, мода по суммам
    - Средний и медианный возраст клиентов
    - Самые популярные марки и типы кузова
    - Данные для графика (выручка по месяцам)
    """
    from .models import Rental, Client, Car

    rentals = Rental.objects.select_related(
        'car__car_model__body_type', 'client', 'discount'
    ).prefetch_related('fines')

    total_count = rentals.count()

    if total_count == 0:
        return {'total_count': 0}

    # ─── Финансовые показатели ────────────────────────────────────────────────
    agg = rentals.aggregate(
        total_revenue=Sum('total_sum'),
        avg_total=Avg('total_sum'),
        max_total=Max('total_sum'),
        min_total=Min('total_sum'),
    )

    total_sums = list(rentals.values_list('total_sum', flat=True))
    total_sums_float = [float(v) for v in total_sums]

    try:
        median_sum = statistics.median(total_sums_float)
        mode_sum = statistics.mode(total_sums_float)
    except statistics.StatisticsError:
        median_sum = None
        mode_sum = None

    # ─── Возраст клиентов ─────────────────────────────────────────────────────
    from django.utils import timezone
    today = timezone.now().date()

    clients_with_rentals = Client.objects.filter(rentals__isnull=False).distinct()
    ages = [
        (today - c.birth_date).days // 365
        for c in clients_with_rentals
    ]

    avg_age = round(sum(ages) / len(ages), 1) if ages else None
    median_age = statistics.median(ages) if ages else None

    # ─── Популярность марок ───────────────────────────────────────────────────
    popular_brands = (
        rentals.values('car__car_model__brand')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # ─── Популярность типов кузова ────────────────────────────────────────────
    popular_body_types = (
        rentals.values('car__car_model__body_type__name')
        .annotate(count=Count('id'), revenue=Sum('total_sum'))
        .order_by('-count')[:5]
    )

    # ─── Выручка по месяцам (для графика) ────────────────────────────────────
    from django.db.models.functions import TruncMonth
    monthly_revenue = (
        rentals.annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(revenue=Sum('total_sum'), count=Count('id'))
        .order_by('month')
    )

    chart_labels = [r['month'].strftime('%m.%Y') for r in monthly_revenue]
    chart_revenue = [float(r['revenue']) for r in monthly_revenue]
    chart_counts = [r['count'] for r in monthly_revenue]

    # ─── Список клиентов по алфавиту ─────────────────────────────────────────
    clients_alpha = (
        Client.objects.annotate(
            total_spent=Sum('rentals__total_sum'),
            rental_count=Count('rentals'),
        )
        .order_by('last_name', 'first_name')
    )

    return {
        'total_count': total_count,
        'total_revenue': agg['total_revenue'],
        'avg_total': round(float(agg['avg_total']), 2) if agg['avg_total'] else 0,
        'median_sum': round(median_sum, 2) if median_sum else 0,
        'mode_sum': round(mode_sum, 2) if mode_sum else 0,
        'max_total': agg['max_total'],
        'min_total': agg['min_total'],
        'avg_age': avg_age,
        'median_age': median_age,
        'popular_brands': list(popular_brands),
        'popular_body_types': list(popular_body_types),
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
        'chart_counts': chart_counts,
        'clients_alpha': clients_alpha,
    }
