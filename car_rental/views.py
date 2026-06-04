import io
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy

from .forms import RentCarForm
from .models import Car, Rental, Client, BodyType
from .services import get_rental_statistics, fetch_random_user, fetch_exchange_rates

logger = logging.getLogger(__name__)


# ─── Публичные CBV ───────────────────────────────────────────────────────────

class CarListView(ListView):
    """Список автомобилей с поиском, фильтром по категории и сортировкой."""
    model = Car
    template_name = 'car_rental/car_list.html'
    context_object_name = 'cars'
    paginate_by = 10

    def get_queryset(self):
        qs = Car.objects.select_related('car_model__body_type', 'car_park')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(license_plate__icontains=q) |
                Q(car_model__brand__icontains=q) |
                Q(car_model__model_name__icontains=q) |
                Q(car_model__body_type__name__icontains=q)
            )

        body_type_id = self.request.GET.get('body_type', '')
        if body_type_id:
            qs = qs.filter(car_model__body_type_id=body_type_id)

        sort = self.request.GET.get('sort', 'brand')
        sort_map = {
            'brand':  'car_model__brand',
            '-brand': '-car_model__brand',
            'price':  'daily_price',
            '-price': '-daily_price',
            'year':   'year',
            '-year':  '-year',
        }
        qs = qs.order_by(sort_map.get(sort, 'car_model__brand'))
        logger.debug('CarListView: q=%s body_type=%s sort=%s count=%s', q, body_type_id, sort, qs.count())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['sort'] = self.request.GET.get('sort', 'brand')
        ctx['body_type_id'] = self.request.GET.get('body_type', '')
        ctx['body_types'] = BodyType.objects.all()
        return ctx


class CarDetailView(DetailView):
    """Карточка автомобиля + курсы валют."""
    model = Car
    template_name = 'car_rental/car_detail.html'
    context_object_name = 'car'

    def get_queryset(self):
        return Car.objects.select_related('car_model__body_type', 'car_park')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['rates'] = fetch_exchange_rates()
        return ctx


class RentCarView(LoginRequiredMixin, CreateView):
    """Оформление проката — только для залогиненных."""
    model = Rental
    form_class = RentCarForm
    template_name = 'car_rental/rent_car.html'
    login_url = '/users/login/'

    def get_car(self):
        return get_object_or_404(Car, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['car'] = self.get_car()
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['car'] = self.get_car()
        return ctx

    def form_valid(self, form):
        car = self.get_car()
        client, created = Client.objects.get_or_create(
            user=self.request.user,
            defaults={
                'last_name': self.request.user.last_name or 'Не указана',
                'first_name': self.request.user.first_name or 'Не указано',
                'address': '',
                'phone': '+375 (29) 000-00-00',
                'birth_date': '2000-01-01',
            },
        )
        rental = form.save(commit=False)
        rental.car = car
        rental.client = client
        rental.save()
        logger.info('Новый прокат #%s: car=%s client=%s', rental.pk, car.license_plate, client)
        messages.success(
            self.request,
            f'Прокат оформлен! Автомобиль {car.car_model} выдан на {rental.days_count} дн. '
            f'Итого: {rental.total_sum} руб.',
        )
        return redirect('car_rental:my_rentals')


class MyRentalsView(LoginRequiredMixin, ListView):
    """Мои прокаты — личный кабинет клиента."""
    model = Rental
    template_name = 'car_rental/my_rentals.html'
    context_object_name = 'rentals'
    login_url = '/users/login/'

    def get_queryset(self):
        try:
            client = self.request.user.client_profile
        except Client.DoesNotExist:
            return Rental.objects.none()
        return (
            Rental.objects
            .filter(client=client)
            .select_related('car__car_model', 'discount')
            .prefetch_related('fines')
            .order_by('-issue_date')
        )


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика — только для staff."""
    template_name = 'car_rental/statistics.html'
    login_url = '/users/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Доступ только для сотрудников.')
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = get_rental_statistics()
        ctx['random_user'] = fetch_random_user()
        ctx['rates'] = fetch_exchange_rates()
        return ctx


# ─── matplotlib PNG-график ───────────────────────────────────────────────────

def statistics_chart(request):
    """PNG-график выручки по месяцам — только staff, без JS."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden()

    monthly = (
        Rental.objects
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(revenue=Sum('total_sum'), count=Count('id'))
        .order_by('month')
    )

    labels   = [r['month'].strftime('%m.%Y') for r in monthly]
    revenues = [float(r['revenue']) for r in monthly]
    counts   = [r['count'] for r in monthly]

    if not labels:
        labels   = ['Нет данных']
        revenues = [0]
        counts   = [0]

    fig, ax1 = plt.subplots(figsize=(12, 5))
    color_bar  = 'steelblue'
    color_line = 'crimson'

    bars = ax1.bar(labels, revenues, color=color_bar, alpha=0.8, label='Выручка (руб.)')
    ax1.set_xlabel('Месяц')
    ax1.set_ylabel('Выручка (руб.)', color=color_bar)
    ax1.tick_params(axis='y', labelcolor=color_bar)
    ax1.tick_params(axis='x', rotation=45)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.5)
    ax1.set_axisbelow(True)

    ax2 = ax1.twinx()
    ax2.plot(labels, counts, color=color_line, marker='o', linewidth=2, label='Прокатов')
    ax2.set_ylabel('Количество прокатов', color=color_line)
    ax2.tick_params(axis='y', labelcolor=color_line)

    max_rev = max(revenues) if revenues else 1
    for bar, val in zip(bars, revenues):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_rev * 0.01,
            f'{val:.0f}',
            ha='center', va='bottom', fontsize=8,
        )

    fig.suptitle('Выручка и количество прокатов по месяцам', fontsize=13, fontweight='bold')
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    logger.info('statistics_chart: сгенерирован (%d месяцев)', len(labels))
    return HttpResponse(buf.read(), content_type='image/png')


# ─── Staff FBV ───────────────────────────────────────────────────────────────

def _staff_required(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if not request.user.is_staff:
        raise PermissionDenied


@login_required(login_url='/users/login/')
def staff_rentals(request):
    """Все прокаты системы — только staff."""
    _staff_required(request)

    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()

    qs = (
        Rental.objects
        .select_related('car__car_model', 'client', 'discount')
        .prefetch_related('fines')
        .order_by('-issue_date')
    )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(
            Q(client__last_name__icontains=q) |
            Q(client__first_name__icontains=q) |
            Q(car__license_plate__icontains=q) |
            Q(car__car_model__brand__icontains=q)
        )

    logger.debug('staff_rentals: count=%s status=%s q=%s', qs.count(), status_filter, q)
    return render(request, 'car_rental/staff_rentals.html', {
        'rentals': qs,
        'status_filter': status_filter,
        'q': q,
        'status_choices': Rental.STATUS_CHOICES,
    })


@login_required(login_url='/users/login/')
def staff_rental_status(request, pk):
    """Изменение статуса проката — только staff, только POST."""
    _staff_required(request)
    rental = get_object_or_404(Rental, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid = dict(Rental.STATUS_CHOICES)
        if new_status in valid:
            Rental.objects.filter(pk=pk).update(status=new_status)
            logger.info('staff_rental_status: #%s → %s (staff=%s)', pk, new_status, request.user)
            messages.success(request, f'Статус проката #{pk} изменён на «{valid[new_status]}».')
        else:
            messages.error(request, 'Недопустимый статус.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and next_url.startswith('http'):
        return redirect(next_url)
    return redirect('car_rental:staff_rentals')


@login_required(login_url='/users/login/')
def staff_clients(request):
    """Список всех клиентов — только staff."""
    _staff_required(request)

    q = request.GET.get('q', '').strip()
    qs = Client.objects.annotate(
        rental_count=Count('rentals'),
        total_spent=Sum('rentals__total_sum'),
    ).order_by('last_name', 'first_name')

    if q:
        qs = qs.filter(
            Q(last_name__icontains=q) |
            Q(first_name__icontains=q) |
            Q(phone__icontains=q)
        )

    logger.debug('staff_clients: count=%s q=%s', qs.count(), q)
    return render(request, 'car_rental/staff_clients.html', {'clients': qs, 'q': q})


@login_required(login_url='/users/login/')
def staff_client_detail(request, pk):
    """Профиль клиента + его прокаты — только staff."""
    _staff_required(request)

    client = get_object_or_404(Client, pk=pk)
    rentals = (
        Rental.objects
        .filter(client=client)
        .select_related('car__car_model', 'discount')
        .prefetch_related('fines')
        .order_by('-issue_date')
    )
    total_spent = rentals.aggregate(total=Sum('total_sum'))['total'] or 0

    logger.debug('staff_client_detail: client=%s rentals=%s', client, rentals.count())
    return render(request, 'car_rental/staff_client_detail.html', {
        'client': client,
        'rentals': rentals,
        'total_spent': total_spent,
        'status_choices': Rental.STATUS_CHOICES,
    })
