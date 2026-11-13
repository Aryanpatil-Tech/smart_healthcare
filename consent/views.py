from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from patients.models import Patient
from .forms import ConsentDecisionForm, ConsentRequestForm
from .models import AccessLog, ConsentRequest
from .services import actor_can_request_access

@login_required
def request_access(request):
    if not actor_can_request_access(request.user):
        raise PermissionDenied("Only verified doctors or approved hospital accounts may request access.")
    patient = None
    if request.method == "POST":
        patient = get_object_or_404(Patient, patient_id=request.POST.get("patient_id", "").strip().upper())
        form = ConsentRequestForm(request.POST)
        if form.is_valid():
            if patient.user_id == request.user.id:
                form.add_error(None, "You cannot request access to your own record.")
            elif not any(form.cleaned_data.get(key) for key in ("history_access", "prescriptions_access", "reports_access", "appointments_access")):
                form.add_error(None, "Select at least one requested category.")
            else:
                consent = form.save(commit=False)
                consent.patient = patient
                consent.requester = request.user
                consent.save()
                AccessLog.objects.create(patient=patient, actor=request.user, action="CONSENT_REQUESTED", details=consent.purpose[:240])
                messages.success(request, "Access request sent. No medical information is available until the patient approves it.")
                return redirect("dashboard:home")
    else:
        form = ConsentRequestForm()
    return render(request, "consent/request.html", {"form": form, "patient": patient})

@login_required
def manage_consent(request):
    if request.user.role != "PATIENT":
        raise PermissionDenied
    patient = request.user.patient_profile
    pending = patient.consent_requests.filter(status=ConsentRequest.Status.PENDING)
    if request.method == "POST":
        consent = get_object_or_404(ConsentRequest, pk=request.POST.get("consent_id"), patient=patient, status=ConsentRequest.Status.PENDING)
        form = ConsentDecisionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["decision"] == "approve":
                days = form.cleaned_data.get("duration_days") or 7
                consent.status = ConsentRequest.Status.APPROVED
                consent.expires_at = timezone.now() + timedelta(days=min(days, 30))
                message = "Access approved with an expiry date."
            else:
                consent.status = ConsentRequest.Status.REJECTED
                message = "Access request rejected."
            consent.responded_at = timezone.now()
            consent.save(update_fields=["status", "expires_at", "responded_at"])
            AccessLog.objects.create(patient=patient, actor=request.user, action=f"CONSENT_{consent.status}", details=f"Request #{consent.pk}")
            messages.success(request, message)
            return redirect("consent:manage")
    active = patient.consent_requests.filter(status=ConsentRequest.Status.APPROVED, expires_at__gt=timezone.now())
    return render(request, "consent/manage.html", {"pending": pending, "active": active})

@login_required
def revoke_consent(request, consent_id):
    if request.method != "POST" or request.user.role != "PATIENT":
        raise PermissionDenied
    consent = get_object_or_404(ConsentRequest, pk=consent_id, patient=request.user.patient_profile, status=ConsentRequest.Status.APPROVED)
    consent.status = ConsentRequest.Status.REVOKED
    consent.responded_at = timezone.now()
    consent.save(update_fields=["status", "responded_at"])
    AccessLog.objects.create(patient=consent.patient, actor=request.user, action="CONSENT_REVOKED", details=f"Request #{consent.pk}")
    messages.success(request, "Permission revoked.")
    return redirect("consent:manage")
