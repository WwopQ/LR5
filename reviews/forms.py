from django import forms

from .models import Review, RATING_CHOICES


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Оценка',
    )

    class Meta:
        model = Review
        fields = ('name', 'rating', 'text')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Напишите ваш отзыв...'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Если пользователь залогинен — подставляем имя и скрываем поле
        if user and user.is_authenticated:
            full_name = user.get_full_name() or user.username
            self.fields['name'].initial = full_name
            self.fields['name'].widget.attrs['readonly'] = True
