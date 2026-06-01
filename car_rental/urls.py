from django.urls import path, re_path

from .views import (
    CarListView, CarDetailView,
    RentCarView, MyRentalsView, StatisticsView,
)

app_name = 'car_rental'

urlpatterns = [
    # Список автомобилей
    path('', CarListView.as_view(), name='car_list'),

    # re_path с регулярным выражением: pk — только целое число (1 и более цифр)
    re_path(r'^(?P<pk>[0-9]+)/$', CarDetailView.as_view(), name='car_detail'),
    re_path(r'^(?P<pk>[0-9]+)/rent/$', RentCarView.as_view(), name='rent_car'),

    # Остальные маршруты через path
    path('my/', MyRentalsView.as_view(), name='my_rentals'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
]
