from django.contrib import admin
from .models import UserProfile, AdminAuditLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'target_resource', 'target_id', 'created_at')
    list_filter = ('action', 'target_resource')
    readonly_fields = ('actor', 'action', 'target_resource', 'target_id', 'details', 'ip_address', 'created_at')