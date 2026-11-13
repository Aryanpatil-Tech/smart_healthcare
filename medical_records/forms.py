from django import forms
from django.db.models import Q
from doctors.models import Doctor
from .models import Appointment, MedicalReport, PrescriptionMedicine, Treatment

class TreatmentCreateForm(forms.ModelForm):
    patient_id = forms.CharField(max_length=20, label="Patient ID")
    class Meta:
        model = Treatment
        fields = ("patient_id", "disease_name", "symptoms", "diagnosis", "treatment_details", "treatment_date", "follow_up_date", "status")
        widgets = {"symptoms": forms.Textarea(attrs={"rows": 3}), "diagnosis": forms.Textarea(attrs={"rows": 3}), "treatment_details": forms.Textarea(attrs={"rows": 3}), "treatment_date": forms.DateInput(attrs={"type": "date"}), "follow_up_date": forms.DateInput(attrs={"type": "date"})}

class MedicineEntryForm(forms.ModelForm):
    class Meta:
        model = PrescriptionMedicine
        fields = ("medicine_name", "dosage", "frequency", "duration", "instructions")

class ReportUploadForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ("title", "report_type", "file")

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        name = uploaded.name.lower()
        uploaded.seek(0)
        signature = uploaded.read(8)
        uploaded.seek(0)

        if name.endswith(".pdf") and not signature.startswith(b"%PDF-"):
            raise forms.ValidationError("The uploaded file does not appear to be a valid PDF.")

        if name.endswith((".png", ".jpg", ".jpeg")):
            # Avoid Pillow for this environment because native image DLLs are blocked on this machine.
            # We still enforce file signature checks for common image formats.
            valid_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
            valid_jpeg = signature.startswith(b"\xff\xd8\xff")
            if not (valid_png or valid_jpeg):
                raise forms.ValidationError("The uploaded image could not be verified.")
            uploaded.seek(0)

        if name.endswith(".txt"):
            try:
                for chunk in uploaded.chunks():
                    chunk.decode("utf-8")
            except UnicodeDecodeError:
                raise forms.ValidationError("Text reports must use UTF-8 encoding.")
            finally:
                uploaded.seek(0)
        return uploaded

class AppointmentCreateForm(forms.ModelForm):
    patient_id = forms.CharField(max_length=20, label="Patient ID")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.role == "PATIENT":
            self.fields.pop("patient_id")
            self.fields["doctor"] = forms.ModelChoiceField(
                queryset=Doctor.objects.filter(verified=True)
                .filter(Q(hospital__isnull=True) | Q(hospital__approved=True))
                .select_related("user", "hospital")
                .order_by("user__last_name", "user__first_name"),
                label="Doctor",
                empty_label="Choose a verified doctor",
            )

    class Meta:
        model = Appointment
        fields = ("patient_id", "scheduled_for", "follow_up_notes")
        widgets = {"scheduled_for": forms.DateTimeInput(attrs={"type": "datetime-local"}), "follow_up_notes": forms.Textarea(attrs={"rows": 2})}
