from django import forms
from django.utils import timezone

from .models import Rental, Car


class RentCarForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ('car', 'discount', 'issue_date', 'days_count')
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'days_count': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, car=None, **kwargs):
        super().__init__(*args, **kwargs)
        if car:
            self.fields['car'].initial = car
            self.fields['car'].widget = forms.HiddenInput()
        self.fields['discount'].required = False
        self.fields['discount'].empty_label = 'Без скидки'
        # Bootstrap-классы
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.HiddenInput):
                continue
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')

    def clean_issue_date(self):
        date = self.cleaned_data['issue_date']
        if date < timezone.now().date():
            raise forms.ValidationError('Дата выдачи не может быть в прошлом.')
        return date
