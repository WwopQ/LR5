from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'is_approved', 'created_at', 'user')
    list_filter = ('is_approved', 'rating')
    list_editable = ('is_approved',)
    search_fields = ('name', 'text', 'user__username')
    readonly_fields = ('created_at', 'user')
    ordering = ('-created_at',)
    fieldsets = (
        ('Автор', {
            'fields': ('user', 'name'),
        }),
        ('Отзыв', {
            'fields': ('rating', 'text'),
        }),
        ('Модерация', {
            'fields': ('is_approved', 'created_at'),
        }),
    )
