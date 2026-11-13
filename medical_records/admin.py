from django.contrib import admin
from .models import Appointment, Disease, MedicalReport, Prescription, PrescriptionMedicine, Treatment

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "disease_name", "doctor", "hospital", "treatment_date", "status")
    list_filter = ("status", "treatment_date")
    search_fields = ("patient__patient_id", "disease_name", "diagnosis")
    readonly_fields = ("created_at",)

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ("title", "patient", "report_type", "uploaded_by", "uploaded_at")
    readonly_fields = ("file", "uploaded_by", "uploaded_at")
    def has_add_permission(self, request): return False

admin.site.register([Disease, Prescription, PrescriptionMedicine, Appointment])
