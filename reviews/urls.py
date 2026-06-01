from django.urls import path

from .views import ReviewListView, AddReviewView

app_name = 'reviews'

urlpatterns = [
    path('', ReviewListView.as_view(), name='list'),
    path('add/', AddReviewView.as_view(), name='add'),
]
