from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from consent.models import AccessLog
from .forms import PatientProfileForm

@login_required
def profile(request):
    if request.user.role != "PATIENT":
        raise PermissionDenied
    patient = request.user.patient_profile
    form = PatientProfileForm(request.POST or None, instance=patient)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("patients:profile")
    return render(request, "patients/profile.html", {"form": form, "patient": patient})

@login_required
def access_logs(request):
    if request.user.role != "PATIENT":
        raise PermissionDenied
    logs = request.user.patient_profile.access_logs.select_related("actor")
    return render(request, "consent/access_logs.html", {"logs": logs})
