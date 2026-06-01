"""
Общие фикстуры для всех тестов.
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone


@pytest.fixture
def user(db):
    """Обычный зарегистрированный пользователь."""
    return User.objects.create_user(
        username='testuser',
        password='TestPass123!',
        first_name='Иван',
        last_name='Иванов',
        email='ivan@example.com',
    )


@pytest.fixture
def staff_user(db):
    """Пользователь-сотрудник (is_staff=True)."""
    return User.objects.create_user(
        username='staffuser',
        password='StaffPass123!',
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    """Суперпользователь."""
    return User.objects.create_superuser(
        username='admin',
        password='AdminPass123!',
        email='admin@example.com',
    )


@pytest.fixture
def auth_client(client, user):
    """Клиент с авторизованным обычным пользователем."""
    client.force_login(user)
    return client


@pytest.fixture
def staff_client(client, staff_user):
    """Клиент с авторизованным сотрудником."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def today():
    return timezone.now().date()


@pytest.fixture
def birth_date_adult():
    """Дата рождения совершеннолетнего (30 лет)."""
    from datetime import date
    today = timezone.now().date()
    return date(today.year - 30, today.month, today.day)
