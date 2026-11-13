from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "user", "blood_group", "created_at")
    search_fields = ("patient_id", "user__first_name", "user__last_name", "user__email")
    readonly_fields = ("patient_id", "lookup_token", "created_at")
