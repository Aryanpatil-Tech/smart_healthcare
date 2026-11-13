from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class HealthUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        DOCTOR = "DOCTOR", "Doctor"
        HOSPITAL = "HOSPITAL", "Hospital"
        STAFF = "STAFF", "Hospital staff"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.PATIENT, db_index=True)
    objects = HealthUserManager()

    def __str__(self):
        return self.get_full_name() or self.username
