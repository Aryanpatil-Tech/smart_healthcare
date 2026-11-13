from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
import qrcode
from qrcode.image.svg import SvgImage
from consent.models import AccessLog
from consent.services import actor_can_request_access, can_access_patient
from medical_records.models import Appointment, Prescription
from patients.models import Patient

def _patient_for_owner(user):
    if user.role != "PATIENT":
        raise PermissionDenied("Only patients can display or download their health card.")
    return get_object_or_404(Patient, user=user)

@login_required
def card(request):
    patient = _patient_for_owner(request.user)
    return render(request, "health_cards/card.html", {"patient": patient})

@login_required
def qr_image(request):
    patient = _patient_for_owner(request.user)
    target = request.build_absolute_uri(reverse("health_cards:scan", args=[patient.lookup_token]))
    image = qrcode.make(
        target,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
        image_factory=SvgImage,
    )
    buffer = BytesIO()
    image.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type="image/svg+xml")
    response["Cache-Control"] = "private, no-store"
    return response

@login_required
def scan(request, token):
    if not actor_can_request_access(request.user):
        raise PermissionDenied("Sign in with a verified doctor or approved hospital account to verify a card.")
    patient = get_object_or_404(Patient.objects.select_related("user"), lookup_token=token)
    AccessLog.objects.create(patient=patient, actor=request.user, action="QR_IDENTITY_LOOKUP", details="Record sections shown only for active approved consent scopes")
    scopes = {
        "history": can_access_patient(request.user, patient, "history"),
        "prescriptions": can_access_patient(request.user, patient, "prescriptions"),
        "reports": can_access_patient(request.user, patient, "reports"),
        "appointments": can_access_patient(request.user, patient, "appointments"),
    }
    context = {"patient": patient, "scopes": scopes, "needs_more_access": not all(scopes.values())}
    if scopes["history"]:
        context["treatments"] = patient.treatments.select_related("doctor__user", "hospital").order_by("-treatment_date")
        AccessLog.objects.create(patient=patient, actor=request.user, action="QR_HISTORY_VIEWED")
    if scopes["prescriptions"]:
        context["prescriptions"] = Prescription.objects.filter(treatment__patient=patient).select_related("treatment").prefetch_related("medicines")
        AccessLog.objects.create(patient=patient, actor=request.user, action="QR_PRESCRIPTIONS_VIEWED")
    if scopes["reports"]:
        context["reports"] = patient.reports.select_related("treatment", "uploaded_by")
        AccessLog.objects.create(patient=patient, actor=request.user, action="QR_REPORTS_VIEWED")
    if scopes["appointments"]:
        context["appointments"] = Appointment.objects.filter(patient=patient).select_related("doctor__user", "hospital")
        AccessLog.objects.create(patient=patient, actor=request.user, action="QR_APPOINTMENTS_VIEWED")
    return render(request, "health_cards/scan_result.html", context)
