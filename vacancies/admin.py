from django.contrib import admin

from .models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
