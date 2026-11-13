from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "registration_number", "hospital", "verified")
    list_filter = ("verified", "specialization")
    search_fields = ("user__first_name", "user__last_name", "registration_number")
    actions = ["verify_selected"]
    @admin.action(description="Verify selected doctor credentials")
    def verify_selected(self, request, queryset): queryset.update(verified=True)
