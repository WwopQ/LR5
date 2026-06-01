import logging

from django.shortcuts import render

from .models import CompanyInfo, Employee

logger = logging.getLogger(__name__)


def home(request):
    """
    Главная страница.
    Показывает краткую информацию о последней опубликованной статье из app news.
    """
    latest_article = None
    try:
        from news.models import Article
        latest_article = (
            Article.objects.filter(is_published=True)
            .order_by('-published_at')
            .first()
        )
    except Exception:
        # Если приложение news ещё не смигрировано — не ломаем главную
        logger.warning('Не удалось получить последнюю статью из news')

    logger.debug('home: last article = %s', latest_article)
    return render(request, 'pages/home.html', {'latest_article': latest_article})


def about(request):
    """Страница «О компании»."""
    company = CompanyInfo.objects.prefetch_related('history').first()
    logger.debug('about: company = %s', company)
    return render(request, 'pages/about.html', {'company': company})


def contacts(request):
    """Страница «Контакты» — список сотрудников."""
    employees = Employee.objects.all()
    logger.debug('contacts: employees count = %s', employees.count())
    return render(request, 'pages/contacts.html', {'employees': employees})


def privacy(request):
    """Страница «Политика конфиденциальности» — пустая заглушка."""
    return render(request, 'pages/privacy.html')
