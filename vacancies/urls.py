from django.urls import path

from .views import VacancyListView

app_name = 'vacancies'

urlpatterns = [
    path('', VacancyListView.as_view(), name='list'),
]
