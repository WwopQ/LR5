from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, validate_phone, validate_age

# Regex для HTML5 pattern (клиентская валидация телефона)
PHONE_PATTERN = r'\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}'


class RegistrationForm(UserCreationForm):
    """
    Форма регистрации: стандартные поля User + поля Profile.
    Валидация: серверная (validators) + клиентская (HTML5 pattern/required/min).
    """

    first_name = forms.CharField(
        max_length=150,
        label='Имя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Иван',
            'required': True,
            'minlength': '2',
            'class': 'form-control',
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'placeholder': 'Иванов',
            'required': True,
            'minlength': '2',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@mail.com',
            'required': True,
        }),
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'placeholder': '+375 (29) XXX-XX-XX',
            'required': True,
            # HTML5 pattern для клиентской валидации формата телефона
            'pattern': PHONE_PATTERN,
            'title': 'Формат: +375 (29) XXX-XX-XX. Коды: 29, 33, 44, 25',
        }),
    )
    birth_date = forms.DateField(
        label='Дата рождения',
        validators=[validate_age],
        widget=forms.DateInput(attrs={
            'type': 'date',
            'required': True,
            # max — дата 18 лет назад (клиентская проверка возраста)
            'max': '',  # заполняется в __init__
        }),
        input_formats=['%Y-%m-%d', '%d.%m.%Y'],
    )
    address = forms.CharField(
        max_length=300,
        required=False,
        label='Адрес',
        widget=forms.TextInput(attrs={
            'placeholder': 'г. Минск, ул. Ленина, д. 1',
        }),
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Клиентская проверка возраста: max = сегодня − 18 лет
        from datetime import date
        from dateutil.relativedelta import relativedelta
        max_date = date.today() - relativedelta(years=18)
        self.fields['birth_date'].widget.attrs['max'] = max_date.strftime('%Y-%m-%d')
        self.fields['password1'].widget.attrs['required'] = True
        self.fields['password2'].widget.attrs['required'] = True
        self.fields['username'].widget.attrs['required'] = True
        # Bootstrap-классы для всех полей
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.EmailInput,
                                   forms.NumberInput, forms.DateInput,
                                   forms.PasswordInput, forms.Textarea)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                birth_date=self.cleaned_data['birth_date'],
                address=self.cleaned_data.get('address', ''),
            )
        return user


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля (имя/фамилия + данные Profile)."""

    first_name = forms.CharField(
        max_length=150, label='Имя',
        widget=forms.TextInput(attrs={'required': True, 'minlength': '2'}),
    )
    last_name = forms.CharField(
        max_length=150, label='Фамилия',
        widget=forms.TextInput(attrs={'required': True, 'minlength': '2'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'required': True}),
    )

    class Meta:
        model = Profile
        fields = ('phone', 'birth_date', 'address')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'required': True}),
            'phone': forms.TextInput(attrs={
                'placeholder': '+375 (29) XXX-XX-XX',
                'required': True,
                'pattern': PHONE_PATTERN,
                'title': 'Формат: +375 (29) XXX-XX-XX. Коды: 29, 33, 44, 25',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        # Ограничение даты рождения (18+) на клиенте
        from datetime import date
        try:
            from dateutil.relativedelta import relativedelta
            max_date = date.today() - relativedelta(years=18)
            self.fields['birth_date'].widget.attrs['max'] = max_date.strftime('%Y-%m-%d')
        except ImportError:
            pass
        # Упорядочиваем поля
        field_order = ['first_name', 'last_name', 'email', 'phone', 'birth_date', 'address']
        self.fields = {k: self.fields[k] for k in field_order if k in self.fields}
        # Bootstrap-классы
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.EmailInput,
                                   forms.DateInput, forms.Textarea)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('Этот email уже занят другим пользователем.')
        return email
