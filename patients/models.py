import secrets
import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

class Patient(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "F", "Female"
        MALE = "M", "Male"
        NON_BINARY = "X", "Non-binary"
        UNSPECIFIED = "U", "Prefer not to say"

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"
        UNKNOWN = "UNK", "Unknown"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile")
    patient_id = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    lookup_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.UNSPECIFIED)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=24, blank=True, validators=[RegexValidator(r"^[+0-9() .-]{7,24}$", "Enter a valid phone number.")])
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = f"PT-{secrets.token_hex(5).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} — {self.user.get_full_name()}"
