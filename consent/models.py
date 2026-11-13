from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

class ConsentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        REVOKED = "REVOKED", "Revoked"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="consent_requests")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="consent_requests")
    history_access = models.BooleanField(default=False)
    prescriptions_access = models.BooleanField(default=False)
    reports_access = models.BooleanField(default=False)
    appointments_access = models.BooleanField(default=False)
    purpose = models.CharField(max_length=240)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        constraints = [models.CheckConstraint(condition=Q(history_access=True) | Q(prescriptions_access=True) | Q(reports_access=True) | Q(appointments_access=True), name="consent_has_scope")]

    def clean(self):
        if not (self.history_access or self.prescriptions_access or self.reports_access or self.appointments_access):
            raise ValidationError("Select at least one information category.")

    def is_active(self, scope=None):
        if self.status != self.Status.APPROVED or not self.expires_at or self.expires_at <= timezone.now():
            return False
        return scope is None or bool(getattr(self, f"{scope}_access", False))

    def __str__(self):
        return f"{self.patient.patient_id} access request from {self.requester}"

class AccessLog(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="access_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="medical_access_logs")
    action = models.CharField(max_length=100)
    details = models.CharField(max_length=240, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-accessed_at"]
        indexes = [models.Index(fields=["patient", "-accessed_at"], name="access_patient_time_idx")]

    def __str__(self):
        return f"{self.actor} — {self.action} — {self.accessed_at:%Y-%m-%d %H:%M}"
