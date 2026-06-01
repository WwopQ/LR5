import pytest
from datetime import date
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User

from users.models import Profile, validate_phone, validate_age
from users.forms import RegistrationForm, ProfileForm


# ─── Валидаторы ───────────────────────────────────────────────────────────────

class TestValidatePhone:
    def test_valid_29(self):
        validate_phone('+375 (29) 123-45-67')  # не должно выбросить

    def test_valid_33(self):
        validate_phone('+375 (33) 987-65-43')

    def test_valid_44(self):
        validate_phone('+375 (44) 111-22-33')

    def test_valid_25(self):
        validate_phone('+375 (25) 000-00-00')

    def test_invalid_no_spaces(self):
        with pytest.raises(ValidationError):
            validate_phone('+375291234567')

    def test_invalid_wrong_code(self):
        with pytest.raises(ValidationError):
            validate_phone('+375 (99) 123-45-67')

    def test_invalid_empty(self):
        with pytest.raises(ValidationError):
            validate_phone('')


class TestValidateAge:
    def test_adult_valid(self):
        today = date.today()
        birth = date(today.year - 25, today.month, today.day)
        validate_age(birth)  # не должно выбросить

    def test_minor_raises(self):
        today = date.today()
        birth = date(today.year - 16, today.month, today.day)
        with pytest.raises(ValidationError, match='18'):
            validate_age(birth)

    def test_exactly_18_valid(self):
        today = date.today()
        birth = date(today.year - 18, today.month, today.day)
        validate_age(birth)


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProfileModel:
    def test_create_and_str(self, user, birth_date_adult):
        profile = Profile.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date=birth_date_adult,
            address='г. Минск',
        )
        assert 'Иван Иванов' in str(profile)

    def test_age_property(self, user, birth_date_adult):
        profile = Profile.objects.create(
            user=user, phone='+375 (29) 123-45-67', birth_date=birth_date_adult
        )
        assert profile.age == 30

    def test_invalid_phone_raises(self, user, birth_date_adult):
        # Django не вызывает validators при create() — нужен явный full_clean()
        p = Profile(
            user=user,
            phone='89001234567',
            birth_date=birth_date_adult,
        )
        with pytest.raises(ValidationError):
            p.full_clean()


# ─── Forms ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrationForm:
    def _valid_data(self):
        today = date.today()
        return {
            'username': 'newuser',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'email': 'new@example.com',
            'phone': '+375 (29) 555-55-55',
            'birth_date': f'{today.year - 25}-06-15',
            'address': 'г. Минск',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }

    def test_valid_form(self):
        form = RegistrationForm(data=self._valid_data())
        assert form.is_valid(), form.errors

    def test_save_creates_user_and_profile(self):
        form = RegistrationForm(data=self._valid_data())
        assert form.is_valid()
        user = form.save()
        assert user.pk is not None
        assert hasattr(user, 'profile')
        assert user.profile.phone == '+375 (29) 555-55-55'

    def test_duplicate_email_invalid(self):
        User.objects.create_user(username='existing', email='new@example.com', password='x')
        form = RegistrationForm(data=self._valid_data())
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_phone_invalid(self):
        data = self._valid_data()
        data['phone'] = '80291234567'
        form = RegistrationForm(data=data)
        assert not form.is_valid()
        assert 'phone' in form.errors

    def test_minor_birth_date_invalid(self):
        data = self._valid_data()
        today = date.today()
        data['birth_date'] = f'{today.year - 15}-01-01'
        form = RegistrationForm(data=data)
        assert not form.is_valid()
        assert 'birth_date' in form.errors


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserViews:
    def test_register_get_200(self, client):
        response = client.get(reverse('users:register'))
        assert response.status_code == 200

    def test_register_authenticated_redirects(self, auth_client):
        response = auth_client.get(reverse('users:register'))
        assert response.status_code == 302

    def test_login_get_200(self, client):
        response = client.get(reverse('users:login'))
        assert response.status_code == 200

    def test_login_post_success(self, client, user):
        response = client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == 302

    def test_login_post_wrong_password(self, client, user):
        response = client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        assert response.status_code == 200
        assert 'Неверный логин' in response.content.decode()

    def test_logout_post(self, auth_client):
        response = auth_client.post(reverse('users:logout'))
        assert response.status_code == 302

    def test_profile_requires_login(self, client):
        response = client.get(reverse('users:profile'))
        assert response.status_code == 302

    def test_profile_authenticated_200(self, auth_client, user, birth_date_adult):
        Profile.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date=birth_date_adult,
        )
        response = auth_client.get(reverse('users:profile'))
        assert response.status_code == 200
