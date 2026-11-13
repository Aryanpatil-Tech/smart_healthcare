from django.conf import settings
from django.db import models

class Hospital(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hospital_profile")
    name = models.CharField(max_length=180)
    registration_number = models.CharField(max_length=80, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=24, blank=True)
    email = models.EmailField(blank=True)
    approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class HospitalStaff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="staff")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "hospital staff"
        constraints = [models.UniqueConstraint(fields=["user", "hospital"], name="unique_hospital_staff_link")]

    def __str__(self):
        return f"{self.user} — {self.hospital}"
