import os
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

ALLOWED_REPORT_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "txt"]

def validate_report_size(upload):
    if upload.size > 10 * 1024 * 1024:
        raise ValidationError("Report files must be 10 MB or smaller.")

def private_report_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"reports/{instance.patient_id}/{uuid.uuid4().hex}{ext}"

class Disease(models.Model):
    name = models.CharField(max_length=180, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Treatment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ongoing"
        FOLLOW_UP = "FOLLOW_UP", "Follow-up required"
        RESOLVED = "RESOLVED", "Resolved"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="treatments")
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.SET_NULL, null=True, related_name="treatments")
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.SET_NULL, null=True, related_name="treatments")
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entered_treatments")
    disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True, related_name="treatments")
    disease_name = models.CharField(max_length=180, blank=True)
    symptoms = models.TextField(blank=True)
    diagnosis = models.TextField()
    treatment_details = models.TextField(blank=True)
    treatment_date = models.DateField(db_index=True)
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-treatment_date", "-created_at"]
        indexes = [models.Index(fields=["patient", "-treatment_date"], name="treatment_patient_date_idx")]

    def __str__(self):
        return f"{self.patient.patient_id}: {self.disease_name or self.diagnosis[:40]}"

class Prescription(models.Model):
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name="prescriptions")
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.treatment}"

class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="medicines")
    medicine_name = models.CharField(max_length=160)
    dosage = models.CharField(max_length=120)
    frequency = models.CharField(max_length=120, blank=True)
    duration = models.CharField(max_length=120)
    instructions = models.CharField(max_length=240, blank=True)

    def __str__(self):
        return self.medicine_name

class MedicalReport(models.Model):
    class ReportType(models.TextChoices):
        LAB = "LAB", "Laboratory"
        XRAY = "XRAY", "X-ray"
        MRI = "MRI", "MRI"
        OTHER = "OTHER", "Other"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="reports")
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=180)
    report_type = models.CharField(max_length=8, choices=ReportType.choices, default=ReportType.OTHER)
    file = models.FileField(upload_to=private_report_path, validators=[FileExtensionValidator(ALLOWED_REPORT_EXTENSIONS), validate_report_size])
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_reports")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def clean(self):
        if self.treatment_id and self.patient_id and self.treatment.patient_id != self.patient_id:
            raise ValidationError("A report must belong to the same patient as its treatment.")

    def __str__(self):
        return self.title

class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.SET_NULL, null=True, related_name="appointments")
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.SET_NULL, null=True, related_name="appointments")
    treatment = models.ForeignKey(Treatment, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    scheduled_for = models.DateTimeField(db_index=True)
    follow_up_notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_for"]

    def __str__(self):
        return f"{self.patient.patient_id} — {self.scheduled_for:%Y-%m-%d %H:%M}"
