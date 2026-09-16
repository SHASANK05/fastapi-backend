from django.db import models
from django.utils import timezone


class CustomUser(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('CUSTOMER', 'Customer'),
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'users'
        managed = False

    def _str_(self):
        return f"{self.name} ({self.role})"


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField()
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'products'
        managed = False

    def _str_(self):
        return f"{self.name} (Stock: {self.stock})"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, db_column='user_id')
    total = models.FloatField()
    order_status = models.CharField(max_length=50, default='PENDING')
    payment_status = models.CharField(max_length=50, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'orders'
        managed = False

    def _str_(self):
        return f"Order #{self.id} - ₹{self.total} ({self.order_status})"