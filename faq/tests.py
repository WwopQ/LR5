import pytest
from django.urls import reverse

from faq.models import FAQ


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFAQModel:
    def test_create_and_str(self):
        faq = FAQ.objects.create(
            question='Что такое прокат?',
            answer='Это временное пользование автомобилем.',
        )
        assert 'Что такое прокат?' in str(faq)
        assert faq.date_added is not None

    def test_str_truncates_long_question(self):
        long_q = 'А' * 100
        faq = FAQ.objects.create(question=long_q, answer='Ответ')
        assert len(str(faq)) <= 80

    def test_ordering_newest_first(self):
        FAQ.objects.create(question='Первый', answer='А')
        FAQ.objects.create(question='Второй', answer='Б')
        first = FAQ.objects.first()
        assert first.question == 'Второй'


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFAQViews:
    def test_list_200(self, client):
        response = client.get(reverse('faq:list'))
        assert response.status_code == 200

    def test_list_shows_faqs(self, client):
        FAQ.objects.create(question='Как арендовать?', answer='Зарегистрируйтесь.')
        response = client.get(reverse('faq:list'))
        assert 'Как арендовать?'.encode() in response.content

    def test_list_empty_no_error(self, client):
        response = client.get(reverse('faq:list'))
        assert response.status_code == 200

    def test_list_template(self, client):
        response = client.get(reverse('faq:list'))
        assert 'faq/faq_list.html' in [t.name for t in response.templates]

    def test_list_context_key(self, client):
        response = client.get(reverse('faq:list'))
        assert 'faqs' in response.context
