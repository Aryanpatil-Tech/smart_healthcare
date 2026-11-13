import mimetypes
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from consent.services import actor_can_request_access
from patients.models import Patient
from .forms import DoctorProfileForm
from .models import Doctor

@login_required
def search_patient(request):
    if not actor_can_request_access(request.user):
        raise PermissionDenied("Your provider account must be verified before searching for patients.")
    patient = None
    if request.method == "GET" and request.GET.get("patient_id"):
        patient = get_object_or_404(Patient.objects.select_related("user"), patient_id=request.GET["patient_id"].strip().upper())
    return render(request, "doctors/search_patient.html", {"patient": patient})

@login_required
def profile(request):
    if request.user.role != "DOCTOR":
        raise PermissionDenied
    doctor = get_object_or_404(Doctor, user=request.user)
    form = DoctorProfileForm(request.POST or None, request.FILES or None, instance=doctor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your professional profile has been updated.")
        return redirect("doctors:profile")
    return render(request, "doctors/profile.html", {"doctor": doctor, "form": form})

@login_required
def photo(request):
    doctor = get_object_or_404(Doctor, user=request.user, verified=True)
    if not doctor.photo:
        raise Http404
    try:
        image = doctor.photo.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404
    response = FileResponse(image, content_type=mimetypes.guess_type(doctor.photo.name)[0] or "application/octet-stream")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
