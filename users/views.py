import logging

from django.contrib import messages, auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RegistrationForm, ProfileForm
from .models import Profile

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect('pages:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info('Зарегистрирован новый пользователь: %s', user.username)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')
            return redirect('pages:home')
        else:
            logger.warning('Ошибка регистрации: %s', form.errors)
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Вход в систему."""
    if request.user.is_authenticated:
        return redirect('pages:home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.info('Вход: %s', user.username)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect(next_url or 'pages:home')
        else:
            logger.warning('Неудачная попытка входа: username=%s', username)
            messages.error(request, 'Неверный логин или пароль.')

    return render(request, 'users/login.html', {'next': next_url})


def logout_view(request):
    """Выход из системы (только POST для защиты от CSRF)."""
    if request.method == 'POST':
        username = request.user.username
        logout(request)
        logger.info('Выход: %s', username)
        messages.info(request, 'Вы вышли из системы.')
    return redirect('pages:home')


@login_required(login_url='/users/login/')
def profile(request):
    """Просмотр и редактирование профиля."""
    user = request.user
    # Получаем или создаём профиль (на случай если создан через админку без профиля)
    profile_obj, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'phone': '+375 (29) 000-00-00', 'birth_date': '2000-01-01'},
    )

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile_obj, user=user)
        if form.is_valid():
            # Обновляем поля User
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            # Сохраняем Profile
            form.save()
            logger.info('Профиль обновлён: %s', user.username)
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('users:profile')
        else:
            logger.warning('Ошибка обновления профиля: %s', form.errors)
    else:
        form = ProfileForm(instance=profile_obj, user=user)

    return render(request, 'users/profile.html', {'form': form, 'profile': profile_obj})
