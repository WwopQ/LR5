"""
Context processors: добавляют данные в контекст каждого шаблона.
"""
import calendar

from django.utils import timezone


def datetime_context(request):
    """
    Добавляет в контекст:
    - current_datetime_local  — текущее время в тайм-зоне пользователя (Europe/Minsk)
    - current_datetime_utc    — текущее время UTC
    - user_timezone           — название тайм-зоны
    - calendar_text           — текстовый календарь на текущий месяц
    """
    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc)

    # Текстовый календарь (недели начинаются с понедельника)
    cal = calendar.TextCalendar(calendar.MONDAY)
    cal_text = cal.formatmonth(now_local.year, now_local.month)

    return {
        'current_datetime_local': now_local,
        'current_datetime_utc': now_utc,
        'user_timezone': str(timezone.get_current_timezone()),
        'calendar_text': cal_text,
    }
