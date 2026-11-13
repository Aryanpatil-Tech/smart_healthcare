import os
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def private_doctor_photo_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f"provider_photos/{uuid.uuid4().hex}{extension}"


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile")
    qualification = models.CharField(max_length=180)
    specialization = models.CharField(max_length=120, db_index=True)
    registration_number = models.CharField(max_length=100, unique=True)
    experience_years = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(80)])
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.SET_NULL, null=True, blank=True, related_name="doctors")
    verified = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    photo = models.FileField(upload_to=private_doctor_photo_path, blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialization})"
