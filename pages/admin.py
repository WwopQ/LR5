from django.contrib import admin

from .models import CompanyInfo, CompanyHistory, Employee


class CompanyHistoryInline(admin.TabularInline):
    """История компании редактируется прямо внутри CompanyInfo."""
    model = CompanyHistory
    extra = 1
    fields = ('year', 'description')
    ordering = ('year',)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyHistoryInline]
    fieldsets = (
        ('Основное', {
            'fields': ('text', 'logo', 'video_url'),
        }),
        ('Реквизиты', {
            'fields': ('requisites',),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        """Запрещаем создание второй записи через админку."""
        return not CompanyInfo.objects.exists()


@admin.register(CompanyHistory)
class CompanyHistoryAdmin(admin.ModelAdmin):
    list_display = ('year', 'description_short', 'company_info')
    list_filter = ('company_info',)
    ordering = ('year',)

    @admin.display(description='Описание')
    def description_short(self, obj):
        return obj.description[:60] + '…' if len(obj.description) > 60 else obj.description


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'phone', 'email', 'birth_date', 'age_display', 'order')
    list_editable = ('order',)
    search_fields = ('last_name', 'first_name', 'position', 'email')
    ordering = ('order', 'last_name')
    readonly_fields = ('age_display',)
    fieldsets = (
        ('ФИО', {
            'fields': ('last_name', 'first_name', 'patronymic'),
        }),
        ('Должность и описание', {
            'fields': ('position', 'description', 'photo'),
        }),
        ('Контакты', {
            'fields': ('phone', 'email'),
        }),
        ('Личные данные (18+)', {
            'fields': ('birth_date', 'age_display'),
        }),
        ('Отображение', {
            'fields': ('order',),
        }),
    )

    @admin.display(description='Возраст')
    def age_display(self, obj):
        if obj.age is not None:
            return f'{obj.age} лет'
        return '—'
