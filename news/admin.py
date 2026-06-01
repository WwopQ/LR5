from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_at', 'created_at', 'updated_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'summary', 'content')
    list_editable = ('is_published',)
    readonly_fields = ('published_at', 'created_at', 'updated_at')
    date_hierarchy = 'published_at'
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'summary', 'content', 'image'),
        }),
        ('Публикация', {
            'fields': ('is_published', 'published_at'),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
