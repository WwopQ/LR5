import pytest
from datetime import date, timedelta
from django.urls import reverse

from promos.models import PromoCode


def make_promo(**kwargs):
    today = date.today()
    defaults = dict(
        code='TEST10',
        discount_pct=10,
        is_active=True,
        valid_from=today - timedelta(days=1),
        valid_to=today + timedelta(days=30),
    )
    defaults.update(kwargs)
    return PromoCode.objects.create(**defaults)


# ─── Модели ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPromoCodeModel:
    def test_create_and_str(self):
        p = make_promo(code='SUMMER', discount_pct=15)
        assert 'SUMMER' in str(p)
        assert '15' in str(p)

    def test_is_currently_valid_true(self):
        p = make_promo()
        assert p.is_currently_valid is True

    def test_is_currently_valid_false_inactive(self):
        p = make_promo(is_active=False)
        assert p.is_currently_valid is False

    def test_is_currently_valid_false_expired(self):
        today = date.today()
        p = make_promo(
            valid_from=today - timedelta(days=10),
            valid_to=today - timedelta(days=1),
        )
        assert p.is_currently_valid is False

    def test_is_currently_valid_false_not_started(self):
        today = date.today()
        p = make_promo(
            valid_from=today + timedelta(days=5),
            valid_to=today + timedelta(days=30),
        )
        assert p.is_currently_valid is False

    def test_code_unique(self):
        make_promo(code='UNIQUE')
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            make_promo(code='UNIQUE')


# ─── Views ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPromoViews:
    def test_list_200(self, client):
        response = client.get(reverse('promos:list'))
        assert response.status_code == 200

    def test_list_shows_active_and_archived(self, client):
        today = date.today()
        make_promo(code='ACTIVE', is_active=True)
        make_promo(
            code='EXPIRED',
            is_active=True,
            valid_from=today - timedelta(days=30),
            valid_to=today - timedelta(days=1),
        )
        response = client.get(reverse('promos:list'))
        assert 'ACTIVE'.encode() in response.content
        assert 'EXPIRED'.encode() in response.content

    def test_list_context_has_active_and_archived(self, client):
        make_promo(code='NOW')
        response = client.get(reverse('promos:list'))
        assert 'active_promos' in response.context
        assert 'archived_promos' in response.context

    def test_list_template(self, client):
        response = client.get(reverse('promos:list'))
        assert 'promos/promo_list.html' in [t.name for t in response.templates]
