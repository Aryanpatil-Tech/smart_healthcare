from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from accounts.models import User
from consent.models import AccessLog, ConsentRequest
from doctors.models import Doctor
from hospitals.models import Hospital
from medical_records.models import Appointment, MedicalReport, Treatment
from patients.models import Patient

def home(request):
    if not request.user.is_authenticated:
        return render(request, "home.html")
    user = request.user
    context = {"user": user}
    if user.is_superuser or user.role == User.Role.ADMIN:
        context.update({"patients_count": Patient.objects.count(), "doctors_pending": Doctor.objects.filter(verified=False).count(), "hospitals_pending": Hospital.objects.filter(approved=False).count(), "treatments_count": Treatment.objects.count(), "recent_logs": AccessLog.objects.select_related("patient", "actor")[:8]})
        template = "dashboard/admin.html"
    elif user.role == User.Role.PATIENT:
        patient = user.patient_profile
        context.update({"patient": patient, "treatment_count": patient.treatments.count(), "report_count": patient.reports.count(), "upcoming": patient.appointments.filter(status="SCHEDULED")[:5], "pending_consents": patient.consent_requests.filter(status=ConsentRequest.Status.PENDING).count()})
        template = "dashboard/patient.html"
    elif user.role == User.Role.DOCTOR:
        doctor = getattr(user, "doctor_profile", None)
        context.update({"doctor": doctor, "verified": bool(doctor and doctor.verified), "treatment_count": doctor.treatments.count() if doctor else 0, "appointments": doctor.appointments.select_related("patient")[:6] if doctor else []})
        template = "dashboard/doctor.html"
    elif user.role in (User.Role.HOSPITAL, User.Role.STAFF):
        hospital = getattr(user, "hospital_profile", None) if user.role == User.Role.HOSPITAL else getattr(getattr(user, "staff_profile", None), "hospital", None)
        context.update({"hospital": hospital, "approved": bool(hospital and hospital.approved), "doctor_count": hospital.doctors.count() if hospital else 0, "treatment_count": hospital.treatments.count() if hospital else 0, "appointments": hospital.appointments.select_related("patient")[:6] if hospital else []})
        template = "dashboard/hospital.html"
    else:
        raise PermissionDenied
    return render(request, template, context)

def about(request):
    return render(request, "about.html")

@login_required
def admin_overview(request):
    if not request.user.is_superuser and request.user.role != User.Role.ADMIN:
        raise PermissionDenied
    context = {"patients_count": Patient.objects.count(), "doctors_pending": Doctor.objects.filter(verified=False).count(), "hospitals_pending": Hospital.objects.filter(approved=False).count(), "treatments_count": Treatment.objects.count(), "users_count": User.objects.count(), "recent_logs": AccessLog.objects.select_related("patient", "actor")[:30]}
    return render(request, "dashboard/admin.html", context)
