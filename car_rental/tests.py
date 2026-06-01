import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse

from car_rental.models import (
    BodyType, CarModel, CarPark, Car, Client, Discount, Fine, Rental,
    validate_phone, validate_age,
)
from django.core.exceptions import ValidationError


# ─── Фикстуры ─────────────────────────────────────────────────────────────────

@pytest.fixture
def body_type(db):
    return BodyType.objects.create(name='Седан')


@pytest.fixture
def car_model(db, body_type):
    return CarModel.objects.create(brand='Toyota', model_name='Camry', body_type=body_type)


@pytest.fixture
def car_park(db):
    return CarPark.objects.create(name='Центральный парк', address='г. Минск, ул. Ленина 1')


@pytest.fixture
def car(db, car_model, car_park):
    return Car.objects.create(
        license_plate='1234 AB-7',
        car_model=car_model,
        car_park=car_park,
        year=2022,
        car_value=Decimal('45000'),
        daily_price=Decimal('100'),
    )


@pytest.fixture
def discount(db):
    return Discount.objects.create(name='Постоянный клиент', percentage=Decimal('10'))


@pytest.fixture
def fine(db):
    return Fine.objects.create(name='Возврат с загрязнением', amount=Decimal('50'))


@pytest.fixture
def client_obj(db, user, birth_date_adult):
    return Client.objects.create(
        user=user,
        last_name='Иванов',
        first_name='Иван',
        patronymic='Иванович',
        address='г. Минск',
        phone='+375 (29) 123-45-67',
        birth_date=birth_date_adult,
    )


@pytest.fixture
def rental(db, car, client_obj):
    return Rental.objects.create(
        car=car,
        client=client_obj,
        issue_date=date.today(),
        days_count=3,
    )


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCarModels:
    def test_body_type_str(self, body_type):
        assert str(body_type) == 'Седан'

    def test_car_model_str(self, car_model):
        assert str(car_model) == 'Toyota Camry'

    def test_car_park_str(self, car_park):
        assert 'Центральный' in str(car_park)

    def test_car_str_contains_plate(self, car):
        assert '1234 AB-7' in str(car)

    def test_car_license_plate_unique(self, car, car_model, car_park):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Car.objects.create(
                license_plate='1234 AB-7',
                car_model=car_model,
                car_park=car_park,
                year=2020,
                car_value=Decimal('30000'),
                daily_price=Decimal('80'),
            )


@pytest.mark.django_db
class TestClientModel:
    def test_str_and_full_name(self, client_obj):
        assert 'Иванов' in str(client_obj)
        assert client_obj.full_name == 'Иванов Иван Иванович'

    def test_full_name_no_patronymic(self, user, birth_date_adult):
        c = Client.objects.create(
            user=user, last_name='Петров', first_name='Пётр',
            address='Минск', phone='+375 (29) 000-00-00',
            birth_date=birth_date_adult,
        )
        assert c.full_name == 'Петров Пётр'

    def test_age_property(self, client_obj):
        assert client_obj.age == 30

    def test_invalid_phone(self, user, birth_date_adult):
        # Django не вызывает validators при create() — нужен явный full_clean()
        c = Client(
            user=user, last_name='Тест', first_name='Тест',
            address='Минск', phone='INVALID',
            birth_date=birth_date_adult,
        )
        with pytest.raises(ValidationError):
            c.full_clean()


@pytest.mark.django_db
class TestDiscountAndFine:
    def test_discount_str(self, discount):
        assert 'Постоянный клиент' in str(discount)
        assert '10' in str(discount)

    def test_fine_str(self, fine):
        assert 'Возврат с загрязнением' in str(fine)
        assert '50' in str(fine)


@pytest.mark.django_db
class TestRentalModel:
    def test_create_calculates_sums(self, rental, car):
        # rental_sum = daily_price * days_count = 100 * 3 = 300
        assert rental.rental_sum == Decimal('300')
        assert rental.discount_sum == Decimal('0')
        assert rental.fine_sum == Decimal('0')
        assert rental.total_sum == Decimal('300')

    def test_expected_return_date(self, rental):
        assert rental.expected_return_date == date.today() + timedelta(days=3)

    def test_with_discount(self, car, client_obj, discount):
        r = Rental.objects.create(
            car=car, client=client_obj,
            issue_date=date.today(), days_count=5,
            discount=discount,
        )
        # rental_sum = 100*5 = 500, discount = 10% → 50, total = 450
        assert r.rental_sum == Decimal('500')
        assert r.discount_sum == Decimal('50')
        assert r.total_sum == Decimal('450')

    def test_add_fine_recalculates(self, rental, fine):
        rental.fines.add(fine)
        rental.refresh_from_db()
        assert rental.fine_sum == Decimal('50')
        assert rental.total_sum == Decimal('350')  # 300 + 50

    def test_remove_fine_recalculates(self, rental, fine):
        rental.fines.add(fine)
        rental.fines.remove(fine)
        rental.refresh_from_db()
        assert rental.fine_sum == Decimal('0')
        assert rental.total_sum == Decimal('300')

    def test_str(self, rental):
        assert 'Прокат #' in str(rental)


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCarListView:
    def test_list_200(self, client, car):
        response = client.get(reverse('car_rental:car_list'))
        assert response.status_code == 200

    def test_list_shows_car(self, client, car):
        response = client.get(reverse('car_rental:car_list'))
        assert 'Toyota'.encode() in response.content

    def test_search_by_brand(self, client, car):
        response = client.get(reverse('car_rental:car_list') + '?q=Toyota')
        assert response.status_code == 200
        assert len(response.context['cars']) == 1

    def test_search_no_results(self, client, car):
        response = client.get(reverse('car_rental:car_list') + '?q=BMW')
        assert len(response.context['cars']) == 0

    def test_sort_by_price(self, client, car_model, car_park):
        Car.objects.create(
            license_plate='AA1', car_model=car_model, car_park=car_park,
            year=2020, car_value=Decimal('30000'), daily_price=Decimal('50'),
        )
        Car.objects.create(
            license_plate='BB2', car_model=car_model, car_park=car_park,
            year=2021, car_value=Decimal('40000'), daily_price=Decimal('200'),
        )
        response = client.get(reverse('car_rental:car_list') + '?sort=price')
        prices = [c.daily_price for c in response.context['cars']]
        assert prices == sorted(prices)

    def test_template(self, client):
        response = client.get(reverse('car_rental:car_list'))
        assert 'car_rental/car_list.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestCarDetailView:
    def test_detail_200(self, client, car):
        response = client.get(reverse('car_rental:car_detail', args=[car.pk]))
        assert response.status_code == 200

    def test_detail_shows_plate(self, client, car):
        response = client.get(reverse('car_rental:car_detail', args=[car.pk]))
        assert '1234 AB-7'.encode() in response.content

    def test_detail_404(self, client):
        response = client.get(reverse('car_rental:car_detail', args=[99999]))
        assert response.status_code == 404


@pytest.mark.django_db
class TestRentCarView:
    def test_rent_requires_login(self, client, car):
        response = client.get(reverse('car_rental:rent_car', args=[car.pk]))
        assert response.status_code == 302
        assert '/users/login/' in response['Location']

    def test_rent_authenticated_200(self, auth_client, car):
        response = auth_client.get(reverse('car_rental:rent_car', args=[car.pk]))
        assert response.status_code == 200

    def test_rent_post_creates_rental(self, auth_client, car, user, birth_date_adult):
        Client.objects.get_or_create(
            user=user,
            defaults={
                'last_name': 'Иванов', 'first_name': 'Иван',
                'address': 'Минск', 'phone': '+375 (29) 123-45-67',
                'birth_date': birth_date_adult,
            },
        )
        response = auth_client.post(reverse('car_rental:rent_car', args=[car.pk]), {
            'car': car.pk,
            'issue_date': date.today().isoformat(),
            'days_count': 2,
        })
        assert response.status_code == 302
        assert Rental.objects.filter(car=car).exists()


@pytest.mark.django_db
class TestMyRentalsView:
    def test_requires_login(self, client):
        response = client.get(reverse('car_rental:my_rentals'))
        assert response.status_code == 302

    def test_authenticated_200(self, auth_client):
        response = auth_client.get(reverse('car_rental:my_rentals'))
        assert response.status_code == 200

    def test_shows_own_rentals(self, auth_client, rental):
        response = auth_client.get(reverse('car_rental:my_rentals'))
        assert response.status_code == 200
        assert 'Toyota' in response.content.decode()


@pytest.mark.django_db
class TestStatisticsView:
    def test_anonymous_redirects(self, client):
        response = client.get(reverse('car_rental:statistics'))
        assert response.status_code == 302

    def test_non_staff_redirects(self, auth_client):
        response = auth_client.get(reverse('car_rental:statistics'))
        assert response.status_code == 302

    def test_staff_200(self, staff_client):
        response = staff_client.get(reverse('car_rental:statistics'))
        assert response.status_code == 200


# ─── Services (без внешних API) ───────────────────────────────────────────────

@pytest.mark.django_db
class TestRentalStatistics:
    def test_empty_stats(self):
        from car_rental.services import get_rental_statistics
        stats = get_rental_statistics()
        assert stats['total_count'] == 0

    def test_stats_with_data(self, rental):
        from car_rental.services import get_rental_statistics
        stats = get_rental_statistics()
        assert stats['total_count'] == 1
        assert stats['total_revenue'] == Decimal('300')
        assert stats['avg_total'] == 300.0
