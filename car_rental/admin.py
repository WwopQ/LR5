from django.contrib import admin
from django.utils.html import format_html

from .models import BodyType, CarModel, CarPark, Car, Client, Discount, Fine, Rental


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model_name', 'body_type')
    list_filter = ('body_type', 'brand')
    search_fields = ('brand', 'model_name')
    ordering = ('brand', 'model_name')


@admin.register(CarPark)
class CarParkAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'car_model', 'year', 'car_park', 'daily_price', 'car_value')
    list_filter = ('car_park', 'car_model__brand', 'car_model__body_type', 'year')
    search_fields = ('license_plate', 'car_model__brand', 'car_model__model_name')
    ordering = ('car_model__brand', 'year')
    fieldsets = (
        ('Идентификация', {
            'fields': ('license_plate', 'car_model', 'year'),
        }),
        ('Фото', {
            'fields': ('photo',),
        }),
        ('Размещение', {
            'fields': ('car_park',),
        }),
        ('Финансы', {
            'fields': ('car_value', 'daily_price'),
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'birth_date', 'age_display', 'address')
    search_fields = ('last_name', 'first_name', 'phone', 'user__username')
    readonly_fields = ('age_display',)
    ordering = ('last_name', 'first_name')

    @admin.display(description='Возраст')
    def age_display(self, obj):
        return f'{obj.age} лет'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount')
    search_fields = ('name',)
    ordering = ('name',)


class RentalFineInline(admin.TabularInline):
    model = Rental.fines.through
    extra = 1
    verbose_name = 'Штраф'
    verbose_name_plural = 'Штрафы проката'


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'car', 'client', 'issue_date', 'days_count',
        'expected_return_date', 'discount', 'rental_sum',
        'discount_sum', 'fine_sum', 'total_sum_colored',
    )
    list_filter = ('issue_date', 'car__car_model__brand', 'discount')
    search_fields = (
        'car__license_plate', 'client__last_name',
        'client__first_name', 'client__phone',
    )
    readonly_fields = (
        'expected_return_date', 'rental_sum', 'discount_sum',
        'fine_sum', 'total_sum', 'created_at', 'updated_at',
    )
    inlines = (RentalFineInline,)
    date_hierarchy = 'issue_date'
    ordering = ('-issue_date',)
    fieldsets = (
        ('Основное', {
            'fields': ('car', 'client', 'discount'),
        }),
        ('Даты', {
            'fields': ('issue_date', 'days_count', 'expected_return_date'),
        }),
        ('Финансы (рассчитываются автоматически)', {
            'fields': ('rental_sum', 'discount_sum', 'fine_sum', 'total_sum'),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Итого (руб.)')
    def total_sum_colored(self, obj):
        color = 'green' if obj.fine_sum == 0 else 'red'
        return format_html('<strong style="color:{}">{}</strong>', color, obj.total_sum)
