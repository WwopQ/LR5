import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy

from .forms import RentCarForm
from .models import Car, Rental, Client
from .services import get_rental_statistics, fetch_random_user, fetch_exchange_rates

logger = logging.getLogger(__name__)


class CarListView(ListView):
    """Список автомобилей с поиском и сортировкой."""
    model = Car
    template_name = 'car_rental/car_list.html'
    context_object_name = 'cars'
    paginate_by = 10

    def get_queryset(self):
        qs = Car.objects.select_related(
            'car_model__body_type', 'car_park'
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(license_plate__icontains=q) |
                Q(car_model__brand__icontains=q) |
                Q(car_model__model_name__icontains=q) |
                Q(car_model__body_type__name__icontains=q)
            )

        sort = self.request.GET.get('sort', 'brand')
        sort_map = {
            'brand':       'car_model__brand',
            '-brand':      '-car_model__brand',
            'price':       'daily_price',
            '-price':      '-daily_price',
            'year':        'year',
            '-year':       '-year',
        }
        qs = qs.order_by(sort_map.get(sort, 'car_model__brand'))
        logger.debug('CarListView: q=%s sort=%s count=%s', q, sort, qs.count())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['sort'] = self.request.GET.get('sort', 'brand')
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
        # Получаем или создаём профиль клиента
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
        logger.info(
            'Новый прокат #%s: car=%s client=%s',
            rental.pk, car.license_plate, client,
        )
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
