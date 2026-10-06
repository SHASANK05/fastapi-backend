from django.db import models
from django.contrib.auth.models import User

class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    cardholder_name = models.CharField(max_length=150)
    masked_card = models.CharField(max_length=19)
    last_4 = models.CharField(max_length=4)
    card_type = models.CharField(max_length=20, default='Visa')
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cardholder_name} - {self.masked_card}"