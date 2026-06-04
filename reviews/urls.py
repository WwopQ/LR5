from django.urls import path

from .views import ReviewListView, AddReviewView, review_delete

app_name = 'reviews'

urlpatterns = [
    path('', ReviewListView.as_view(), name='list'),
    path('add/', AddReviewView.as_view(), name='add'),
    path('<int:pk>/delete/', review_delete, name='delete'),
]
