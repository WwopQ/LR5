from django.urls import path, re_path

from .views import (
    CarListView, CarDetailView,
    RentCarView, MyRentalsView, StatisticsView,
    statistics_chart,
    staff_rentals, staff_rental_status,
    staff_clients, staff_client_detail,
)

app_name = 'car_rental'

urlpatterns = [
    # Список и карточка автомобилей
    path('', CarListView.as_view(), name='car_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', CarDetailView.as_view(), name='car_detail'),
    re_path(r'^(?P<pk>[0-9]+)/rent/$', RentCarView.as_view(), name='rent_car'),

    # Личный кабинет клиента
    path('my/', MyRentalsView.as_view(), name='my_rentals'),

    # Статистика (CBV) и график (FBV)
    path('statistics/', StatisticsView.as_view(), name='statistics'),
    path('statistics/chart.png', statistics_chart, name='statistics_chart'),

    # Staff-интерфейс (FBV)
    path('staff/rentals/', staff_rentals, name='staff_rentals'),
    path('staff/rentals/<int:pk>/status/', staff_rental_status, name='staff_rental_status'),
    path('staff/clients/', staff_clients, name='staff_clients'),
    path('staff/clients/<int:pk>/', staff_client_detail, name='staff_client_detail'),
]
