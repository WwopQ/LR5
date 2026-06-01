from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, validate_phone, validate_age


class RegistrationForm(UserCreationForm):
    """Форма регистрации: стандартные поля User + поля Profile."""

    first_name = forms.CharField(
        max_length=150,
        label='Имя',
        widget=forms.TextInput(attrs={'placeholder': 'Иван'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Фамилия',
        widget=forms.TextInput(attrs={'placeholder': 'Иванов'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.com'}),
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        validators=[validate_phone],
        widget=forms.TextInput(attrs={'placeholder': '+375 (29) XXX-XX-XX'}),
    )
    birth_date = forms.DateField(
        label='Дата рождения',
        validators=[validate_age],
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d.%m.%Y'],
    )
    address = forms.CharField(
        max_length=300,
        required=False,
        label='Адрес',
        widget=forms.TextInput(attrs={'placeholder': 'г. Минск, ул. Ленина, д. 1'}),
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2',
        )

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

    first_name = forms.CharField(max_length=150, label='Имя')
    last_name = forms.CharField(max_length=150, label='Фамилия')
    email = forms.EmailField(label='Email')

    class Meta:
        model = Profile
        fields = ('phone', 'birth_date', 'address')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+375 (29) XXX-XX-XX'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        # Упорядочиваем поля
        field_order = ['first_name', 'last_name', 'email', 'phone', 'birth_date', 'address']
        self.fields = {k: self.fields[k] for k in field_order if k in self.fields}

    def clean_email(self):
        email = self.cleaned_data['email']
        # Проверяем уникальность, исключая текущего пользователя
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('Этот email уже занят другим пользователем.')
        return email
