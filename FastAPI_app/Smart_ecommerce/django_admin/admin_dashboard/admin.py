from django.contrib import admin
from .models import User, Product, Order,ReturnRequest

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'role', 'created_at')
    search_fields = ('email',)
    list_filter = ('role',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock', 'created_at')
    list_editable = ('price', 'stock')
    list_filter = ('category',)
    search_fields = ('name', 'category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'order_status', 'payment_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'created_at')
    list_editable = ('order_status', 'payment_status')
    search_fields = ('user__email',)

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'reason', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('order_id', 'user__email', 'reason')