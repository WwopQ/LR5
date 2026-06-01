import logging

from django.views.generic import ListView

from .models import Vacancy

logger = logging.getLogger(__name__)


class VacancyListView(ListView):
    model = Vacancy
    template_name = 'vacancies/vacancy_list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        # По умолчанию — только активные; admin видит все через отдельный интерфейс
        qs = Vacancy.objects.filter(is_active=True)
        logger.debug('VacancyListView: активных вакансий = %s', qs.count())
        return qs
