from django.utils import timezone
from doctors.models import Doctor
from hospitals.models import Hospital, HospitalStaff
from .models import ConsentRequest

def actor_can_request_access(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if user.role == "DOCTOR":
        return Doctor.objects.filter(user=user, verified=True, hospital__approved=True).exists() or Doctor.objects.filter(user=user, verified=True, hospital__isnull=True).exists()
    if user.role == "HOSPITAL":
        return Hospital.objects.filter(user=user, approved=True).exists()
    if user.role == "STAFF":
        return HospitalStaff.objects.filter(user=user, active=True, hospital__approved=True).exists()
    return False

def has_consent(user, patient, scope):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return ConsentRequest.objects.filter(patient=patient, requester=user, status=ConsentRequest.Status.APPROVED, expires_at__gt=timezone.now(), **{f"{scope}_access": True}).exists()

def can_access_patient(user, patient, scope):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.role == "PATIENT":
        return getattr(user, "patient_profile", None) == patient
    return has_consent(user, patient, scope)
