import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        qs = Review.objects.filter(is_approved=True).select_related('user')
        logger.debug('ReviewListView: одобренных отзывов = %s', qs.count())
        return qs


class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/add_review.html'
    success_url = reverse_lazy('reviews:list')
    # Незалогиненных перенаправляем на страницу входа
    login_url = '/users/login/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        review = form.save(commit=False)
        review.user = self.request.user
        # Имя берём из профиля, если поле не заполнено вручную
        if not review.name:
            review.name = self.request.user.get_full_name() or self.request.user.username
        review.save()
        logger.info('Новый отзыв от user=%s, rating=%s', self.request.user, review.rating)
        messages.success(
            self.request,
            'Спасибо за отзыв! Он появится на сайте после проверки модератором.',
        )
        return super().form_valid(form)
