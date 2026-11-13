from django.contrib import admin
from .models import AccessLog, ConsentRequest

@admin.register(ConsentRequest)
class ConsentRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "requester", "status", "history_access", "prescriptions_access", "reports_access", "expires_at")
    list_filter = ("status", "history_access", "prescriptions_access", "reports_access")
    readonly_fields = ("requested_at", "responded_at")

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("patient", "actor", "action", "accessed_at")
    list_filter = ("action", "accessed_at")
    readonly_fields = ("patient", "actor", "action", "details", "accessed_at")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
