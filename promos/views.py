import logging

from django.utils import timezone
from django.views.generic import ListView

from .models import PromoCode

logger = logging.getLogger(__name__)


class PromoListView(ListView):
    model = PromoCode
    template_name = 'promos/promo_list.html'
    context_object_name = 'promos'

    def get_queryset(self):
        return PromoCode.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        all_promos = self.get_queryset()

        # Действующие: активны и в диапазоне дат
        context['active_promos'] = all_promos.filter(
            is_active=True,
            valid_from__lte=today,
            valid_to__gte=today,
        )
        # Архив: неактивны или срок истёк
        context['archived_promos'] = all_promos.exclude(
            is_active=True,
            valid_from__lte=today,
            valid_to__gte=today,
        )
        logger.debug(
            'PromoListView: действующих=%s, в архиве=%s',
            context['active_promos'].count(),
            context['archived_promos'].count(),
        )
        return context
