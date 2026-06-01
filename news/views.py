import logging

from django.views.generic import ListView, DetailView

from .models import Article

logger = logging.getLogger(__name__)


class NewsListView(ListView):
    model = Article
    template_name = 'news/news_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        qs = Article.objects.filter(is_published=True).order_by('-published_at')
        logger.debug('NewsListView: найдено статей = %s', qs.count())
        return qs


class NewsDetailView(DetailView):
    model = Article
    template_name = 'news/news_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        # Обычные пользователи видят только опубликованные;
        # сотрудники и суперюзеры — любые (для предпросмотра)
        if self.request.user.is_staff:
            return Article.objects.all()
        return Article.objects.filter(is_published=True)

    def get(self, request, *args, **kwargs):
        logger.debug('NewsDetailView: pk=%s, user=%s', kwargs.get('pk'), request.user)
        return super().get(request, *args, **kwargs)
