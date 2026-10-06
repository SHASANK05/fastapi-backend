from django.contrib import admin
from .models import Card

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'cardholder_name', 'masked_card', 'card_type', 'expiry_month', 'expiry_year', 'created_at')
    list_filter = ('card_type', 'created_at')
    search_fields = ('cardholder_name', 'last_4', 'user__username')