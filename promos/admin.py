from django.contrib import admin
from django.utils import timezone

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_pct', 'is_active', 'valid_from', 'valid_to', 'status')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('code', 'description')
    ordering = ('-valid_to',)

    @admin.display(description='Статус')
    def status(self, obj):
        today = timezone.now().date()
        if not obj.is_active:
            return 'Архив'
        if today < obj.valid_from:
            return 'Ещё не начался'
        if today > obj.valid_to:
            return 'Истёк'
        return 'Действует'
