import pytest
from django.urls import reverse

from reviews.models import Review
from reviews.forms import ReviewForm


def make_review(user=None, **kwargs):
    defaults = dict(name='Тест Тестов', rating=5, text='Отличный сервис!', is_approved=True)
    defaults.update(kwargs)
    if user:
        defaults['user'] = user
    return Review.objects.create(**defaults)


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewModel:
    def test_create_and_str(self):
        r = make_review(name='Иван', rating=4)
        assert 'Иван' in str(r)
        assert '4/5' in str(r)

    def test_default_not_approved(self):
        r = Review.objects.create(name='Тест', rating=3, text='Нормально')
        assert r.is_approved is False

    def test_user_nullable(self):
        r = make_review()
        assert r.user is None

    def test_ordering_newest_first(self):
        make_review(name='Первый')
        make_review(name='Второй')
        assert Review.objects.first().name == 'Второй'


# ─── Forms ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewForm:
    def test_valid_form(self):
        form = ReviewForm(data={'name': 'Тест', 'rating': 5, 'text': 'Хорошо'})
        assert form.is_valid(), form.errors

    def test_invalid_rating_zero(self):
        form = ReviewForm(data={'name': 'Тест', 'rating': 0, 'text': 'Текст'})
        assert not form.is_valid()

    def test_invalid_rating_six(self):
        form = ReviewForm(data={'name': 'Тест', 'rating': 6, 'text': 'Текст'})
        assert not form.is_valid()

    def test_name_prefilled_for_authenticated_user(self, user):
        form = ReviewForm(user=user)
        assert form.fields['name'].initial == 'Иван Иванов'

    def test_name_field_readonly_for_authenticated_user(self, user):
        form = ReviewForm(user=user)
        assert form.fields['name'].widget.attrs.get('readonly')


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewViews:
    def test_list_200(self, client):
        response = client.get(reverse('reviews:list'))
        assert response.status_code == 200

    def test_list_shows_only_approved(self, client):
        make_review(name='Одобренный', is_approved=True)
        make_review(name='Неодобренный', is_approved=False)
        response = client.get(reverse('reviews:list'))
        assert 'Одобренный'.encode() in response.content
        assert 'Неодобренный'.encode() not in response.content

    def test_add_review_requires_login(self, client):
        response = client.get(reverse('reviews:add'))
        assert response.status_code == 302
        assert '/users/login/' in response['Location']

    def test_add_review_authenticated_200(self, auth_client):
        response = auth_client.get(reverse('reviews:add'))
        assert response.status_code == 200

    def test_add_review_post_creates_review(self, auth_client, user):
        response = auth_client.post(reverse('reviews:add'), {
            'name': 'Тест Тестов',
            'rating': 5,
            'text': 'Очень доволен прокатом!',
        })
        assert response.status_code == 302
        assert Review.objects.filter(user=user).exists()

    def test_add_review_not_approved_by_default(self, auth_client, user):
        auth_client.post(reverse('reviews:add'), {
            'name': 'Тест', 'rating': 4, 'text': 'Хорошо',
        })
        r = Review.objects.filter(user=user).first()
        assert r is not None
        assert r.is_approved is False
