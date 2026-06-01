import logging

from django.views.generic import ListView

from .models import FAQ

logger = logging.getLogger(__name__)


class FAQListView(ListView):
    model = FAQ
    template_name = 'faq/faq_list.html'
    context_object_name = 'faqs'

    def get_queryset(self):
        qs = FAQ.objects.all()
        logger.debug('FAQListView: записей = %s', qs.count())
        return qs
