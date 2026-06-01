import pytest
from django.urls import reverse
from django.utils import timezone

from news.models import Article


def make_article(**kwargs):
    defaults = dict(
        title='Заголовок',
        summary='Краткое содержание статьи.',
        content='Полный текст статьи.',
        is_published=True,
    )
    defaults.update(kwargs)
    return Article.objects.create(**defaults)


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestArticleModel:
    def test_create_and_str(self):
        a = make_article(title='Тест')
        assert str(a) == 'Тест'
        assert a.pk is not None

    def test_published_at_set_on_publish(self):
        a = make_article(is_published=True, published_at=None)
        assert a.published_at is not None

    def test_published_at_not_overwritten(self):
        fixed = timezone.now()
        a = make_article(is_published=True, published_at=fixed)
        # Повторно сохраняем — дата не должна сброситься
        a.title = 'Новый заголовок'
        a.save()
        assert a.published_at == fixed

    def test_unpublished_has_no_published_at(self):
        a = make_article(is_published=False)
        assert a.published_at is None

    def test_ordering_newest_first(self):
        a1 = make_article(title='Первая')
        a2 = make_article(title='Вторая')
        titles = list(Article.objects.values_list('title', flat=True))
        # Сортировка по -published_at: вторая статья новее
        assert titles[0] == 'Вторая'


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNewsViews:
    def test_list_200(self, client):
        response = client.get(reverse('news:list'))
        assert response.status_code == 200

    def test_list_shows_only_published(self, client):
        make_article(title='Опубликована', is_published=True)
        make_article(title='Черновик', is_published=False)
        response = client.get(reverse('news:list'))
        assert 'Опубликована'.encode() in response.content
        assert 'Черновик'.encode() not in response.content

    def test_list_empty(self, client):
        response = client.get(reverse('news:list'))
        assert response.status_code == 200

    def test_detail_200(self, client):
        a = make_article()
        response = client.get(reverse('news:detail', args=[a.pk]))
        assert response.status_code == 200

    def test_detail_title_in_content(self, client):
        a = make_article(title='Уникальный заголовок 9999')
        response = client.get(reverse('news:detail', args=[a.pk]))
        assert 'Уникальный заголовок 9999'.encode() in response.content

    def test_detail_unpublished_anonymous_404(self, client):
        a = make_article(is_published=False)
        response = client.get(reverse('news:detail', args=[a.pk]))
        assert response.status_code == 404

    def test_detail_unpublished_staff_200(self, staff_client):
        a = make_article(is_published=False)
        response = staff_client.get(reverse('news:detail', args=[a.pk]))
        assert response.status_code == 200

    def test_list_pagination(self, client):
        for i in range(12):
            make_article(title=f'Статья {i}')
        response = client.get(reverse('news:list'))
        assert response.status_code == 200
        # На первой странице 10 статей
        assert len(response.context['articles']) == 10
