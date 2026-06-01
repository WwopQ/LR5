import pytest
from django.urls import reverse

from vacancies.models import Vacancy


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVacancyModel:
    def test_create_and_str(self):
        v = Vacancy.objects.create(title='Менеджер по прокату', description='Обязанности...')
        assert 'Менеджер по прокату' in str(v)
        assert 'активна' in str(v)

    def test_archive_str(self):
        v = Vacancy.objects.create(title='Водитель', description='...', is_active=False)
        assert 'архив' in str(v)

    def test_default_is_active_true(self):
        v = Vacancy.objects.create(title='Тест', description='Описание')
        assert v.is_active is True

    def test_ordering_newest_first(self):
        Vacancy.objects.create(title='Первая', description='...')
        Vacancy.objects.create(title='Вторая', description='...')
        first = Vacancy.objects.first()
        assert first.title == 'Вторая'


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVacancyViews:
    def test_list_200(self, client):
        response = client.get(reverse('vacancies:list'))
        assert response.status_code == 200

    def test_list_shows_only_active(self, client):
        Vacancy.objects.create(title='Активная', description='...', is_active=True)
        Vacancy.objects.create(title='Архивная', description='...', is_active=False)
        response = client.get(reverse('vacancies:list'))
        assert 'Активная'.encode() in response.content
        assert 'Архивная'.encode() not in response.content

    def test_list_template(self, client):
        response = client.get(reverse('vacancies:list'))
        assert 'vacancies/vacancy_list.html' in [t.name for t in response.templates]

    def test_list_context_key(self, client):
        response = client.get(reverse('vacancies:list'))
        assert 'vacancies' in response.context
