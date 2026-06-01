from django.contrib import admin

from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'date_added')
    search_fields = ('question', 'answer')
    readonly_fields = ('date_added',)
    ordering = ('-date_added',)

    @admin.display(description='Вопрос')
    def question_short(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
