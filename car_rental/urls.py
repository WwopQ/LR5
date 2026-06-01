from django.urls import path

from .views import (
    CarListView, CarDetailView,
    RentCarView, MyRentalsView, StatisticsView,
)

app_name = 'car_rental'

urlpatterns = [
    path('', CarListView.as_view(), name='car_list'),
    path('<int:pk>/', CarDetailView.as_view(), name='car_detail'),
    path('<int:pk>/rent/', RentCarView.as_view(), name='rent_car'),
    path('my/', MyRentalsView.as_view(), name='my_rentals'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
]
