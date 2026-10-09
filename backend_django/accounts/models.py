from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        SUPPORT = 'SUPPORT', 'Support'
        READ_ONLY = 'READ_ONLY', 'Read-Only'
        CUSTOMER = 'CUSTOMER', 'Customer'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# Automatically create or update UserProfile whenever a User is created
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        # Default superusers to ADMIN, regular users to CUSTOMER
        default_role = UserProfile.Role.ADMIN if instance.is_superuser else UserProfile.Role.CUSTOMER
        UserProfile.objects.create(user=instance, role=default_role)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class AdminAuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_actions')
    action = models.CharField(max_length=64)  # e.g., 'BLOCK_CARD', 'UPDATE_LIMIT'
    target_resource = models.CharField(max_length=64)  # e.g., 'CARD', 'USER'
    target_id = models.IntegerField()
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at}] {self.actor.username} -> {self.action} on {self.target_resource}#{self.target_id}"