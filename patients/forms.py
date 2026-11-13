from django import forms
from .models import Patient

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ("date_of_birth", "gender", "blood_group", "address", "emergency_contact_name", "emergency_contact_phone")
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "address": forms.Textarea(attrs={"rows": 3})}
