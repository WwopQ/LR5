from django.urls import path

from .views import PromoListView

app_name = 'promos'

urlpatterns = [
    path('', PromoListView.as_view(), name='list'),
]
