from django.contrib import admin
from .models import CustomUser, Product, Order


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('name', 'email')
    list_editable = ('role',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'created_at')
    list_editable = ('price', 'stock')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'order_status', 'payment_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'created_at')
    list_editable = ('order_status', 'payment_status')
    search_fields = ('user__name', 'user__email')