import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from pages.models import CompanyInfo, CompanyHistory, Employee


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyInfo:
    def test_create(self):
        info = CompanyInfo.objects.create(text='О нашей компании')
        assert info.pk is not None
        assert str(info) == 'О компании'

    def test_singleton_raises(self):
        CompanyInfo.objects.create(text='Первая запись')
        with pytest.raises(ValidationError, match='одна запись'):
            CompanyInfo.objects.create(text='Вторая запись')

    def test_optional_fields_blank(self):
        info = CompanyInfo.objects.create(text='Текст')
        assert info.video_url == ''
        assert info.logo.name is None or info.logo.name == ''


@pytest.mark.django_db
class TestCompanyHistory:
    def test_create_and_str(self):
        info = CompanyInfo.objects.create(text='Текст')
        event = CompanyHistory.objects.create(
            company_info=info, year=2020, description='Основание компании'
        )
        assert '2020' in str(event)
        assert 'Основание' in str(event)

    def test_ordering_by_year(self):
        info = CompanyInfo.objects.create(text='Текст')
        CompanyHistory.objects.create(company_info=info, year=2022, description='Позже')
        CompanyHistory.objects.create(company_info=info, year=2018, description='Раньше')
        years = list(CompanyHistory.objects.values_list('year', flat=True))
        assert years == [2018, 2022]


@pytest.mark.django_db
class TestEmployee:
    def test_create_and_full_name(self):
        emp = Employee.objects.create(
            last_name='Петров', first_name='Пётр', patronymic='Петрович',
            position='Менеджер',
        )
        assert emp.full_name == 'Петров Пётр Петрович'
        assert str(emp) == 'Петров Пётр — Менеджер'

    def test_full_name_without_patronymic(self):
        emp = Employee.objects.create(
            last_name='Иванов', first_name='Иван', position='Директор'
        )
        assert emp.full_name == 'Иванов Иван'

    def test_ordering_by_order_then_last_name(self):
        Employee.objects.create(last_name='Б', first_name='Б', position='P', order=2)
        Employee.objects.create(last_name='А', first_name='А', position='P', order=1)
        names = list(Employee.objects.values_list('last_name', flat=True))
        assert names == ['А', 'Б']


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPagesViews:
    def test_home_200(self, client):
        url = reverse('pages:home')
        response = client.get(url)
        assert response.status_code == 200
        assert b'RentCar' in response.content

    def test_home_template(self, client):
        url = reverse('pages:home')
        response = client.get(url)
        assert 'pages/home.html' in [t.name for t in response.templates]

    def test_about_200(self, client):
        response = client.get(reverse('pages:about'))
        assert response.status_code == 200

    def test_about_shows_company_info(self, client):
        CompanyInfo.objects.create(text='Мы крутая компания')
        response = client.get(reverse('pages:about'))
        assert 'Мы крутая компания'.encode() in response.content

    def test_contacts_200(self, client):
        response = client.get(reverse('pages:contacts'))
        assert response.status_code == 200

    def test_contacts_shows_employees(self, client):
        Employee.objects.create(
            last_name='Тест', first_name='Тест', position='Тестировщик'
        )
        response = client.get(reverse('pages:contacts'))
        assert 'Тестировщик' in response.content.decode()

    def test_privacy_200(self, client):
        response = client.get(reverse('pages:privacy'))
        assert response.status_code == 200
