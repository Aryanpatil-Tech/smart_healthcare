from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User
from patients.models import Patient
from doctors.models import Doctor
from hospitals.models import Hospital

class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(choices=Patient.Gender.choices)
    blood_group = forms.ChoiceField(choices=Patient.BloodGroup.choices)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        if commit:
            user.save()
            Patient.objects.create(user=user, date_of_birth=self.cleaned_data.get("date_of_birth"), gender=self.cleaned_data["gender"], blood_group=self.cleaned_data["blood_group"])
        return user

class DoctorRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    qualification = forms.CharField(max_length=180)
    specialization = forms.CharField(max_length=120)
    registration_number = forms.CharField(max_length=100)
    experience_years = forms.IntegerField(min_value=0, max_value=80)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR
        if commit:
            user.save()
            Doctor.objects.create(user=user, qualification=self.cleaned_data["qualification"], specialization=self.cleaned_data["specialization"], registration_number=self.cleaned_data["registration_number"], experience_years=self.cleaned_data["experience_years"])
        return user

class HospitalRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, label="Administrator first name")
    last_name = forms.CharField(max_length=150, label="Administrator last name")
    hospital_name = forms.CharField(max_length=180)
    registration_number = forms.CharField(max_length=80)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    phone = forms.CharField(max_length=24, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.HOSPITAL
        if commit:
            user.save()
            Hospital.objects.create(user=user, name=self.cleaned_data["hospital_name"], registration_number=self.cleaned_data["registration_number"], address=self.cleaned_data["address"], phone=self.cleaned_data["phone"], email=self.cleaned_data["email"])
        return user
