from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import DoctorRegistrationForm, HospitalRegistrationForm, PatientRegistrationForm
from .models import User

ROLE_LABELS = {"PATIENT": "Patient", "DOCTOR": "Doctor", "HOSPITAL": "Hospital", "ADMIN": "Administrator"}

def login_view(request, expected_role=None):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    error = ""
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", "").strip(), password=request.POST.get("password", ""))
        if user is not None and (expected_role is None or user.role == expected_role or (expected_role == "ADMIN" and user.is_superuser)):
            login(request, user)
            return redirect("dashboard:home")
        error = "The username or password was not accepted for this account type."
    title = ROLE_LABELS.get(expected_role, "Account")
    return render(request, "registration/login.html", {"error": error, "title": title, "expected_role": expected_role})

def register_patient(request):
    return _register(request, PatientRegistrationForm, "registration/register.html", "Patient registration")

def register_doctor(request):
    return _register(request, DoctorRegistrationForm, "registration/register.html", "Doctor application")

def register_hospital(request):
    return _register(request, HospitalRegistrationForm, "registration/register.html", "Hospital application")

def _register(request, form_class, template, title):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, "Account created. Provider accounts remain pending administrator verification or approval.")
        login(request, user)
        return redirect("dashboard:home")
    return render(request, template, {"form": form, "title": title})

@login_required
def logout_view(request):
    if request.method != "POST":
        return redirect("dashboard:home")
    logout(request)
    messages.info(request, "You have been securely signed out.")
    return redirect("home")
