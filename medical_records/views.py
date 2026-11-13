import os
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from consent.models import AccessLog
from consent.services import actor_can_request_access, can_access_patient
from doctors.models import Doctor
from hospitals.models import Hospital, HospitalStaff
from patients.models import Patient
from .forms import AppointmentCreateForm, MedicineEntryForm, ReportUploadForm, TreatmentCreateForm
from .models import Appointment, Disease, MedicalReport, Prescription, PrescriptionMedicine, Treatment

def _log_view(user, patient, action, details=""):
    if user.role != "PATIENT" and not user.is_superuser:
        AccessLog.objects.create(patient=patient, actor=user, action=action, details=details[:240])

def _provider_context(user):
    if not actor_can_request_access(user):
        raise PermissionDenied("A verified doctor or approved hospital account is required.")
    doctor = Doctor.objects.filter(user=user, verified=True).first() if user.role == "DOCTOR" else None
    if doctor and doctor.hospital_id and not doctor.hospital.approved:
        doctor = None
    hospital = Hospital.objects.filter(user=user, approved=True).first() if user.role == "HOSPITAL" else None
    if user.role == "STAFF":
        staff = HospitalStaff.objects.filter(user=user, active=True, hospital__approved=True).select_related("hospital").first()
        hospital = staff.hospital if staff else None
    if not doctor and not hospital:
        raise PermissionDenied("A verified doctor or approved hospital account is required.")
    return doctor, hospital

@login_required
def history(request):
    patient = request.user.patient_profile if request.user.role == "PATIENT" else None
    patient_id = request.GET.get("patient_id", "")
    if patient is None:
        if not patient_id:
            return render(request, "records/history.html", {"needs_search": True})
        patient = get_object_or_404(Patient, patient_id=patient_id.strip().upper())
        if not can_access_patient(request.user, patient, "history"):
            raise PermissionDenied("Patient consent for medical history is required.")
        _log_view(request.user, patient, "MEDICAL_HISTORY_VIEWED")
    elif not can_access_patient(request.user, patient, "history"):
        raise PermissionDenied
    treatments = patient.treatments.select_related("doctor__user", "hospital", "disease").prefetch_related("prescriptions__medicines", "reports")
    show_prescriptions = request.user.role == "PATIENT" or can_access_patient(request.user, patient, "prescriptions")
    show_reports = request.user.role == "PATIENT" or can_access_patient(request.user, patient, "reports")
    return render(request, "records/history.html", {"patient": patient, "treatments": treatments, "show_prescriptions": show_prescriptions, "show_reports": show_reports})

@login_required
def prescriptions(request):
    patient_id = request.GET.get("patient_id", "")
    if request.user.role == "PATIENT":
        patient = request.user.patient_profile
    elif patient_id:
        patient = get_object_or_404(Patient, patient_id=patient_id.strip().upper())
        if not can_access_patient(request.user, patient, "prescriptions"):
            raise PermissionDenied("Patient prescription consent is required.")
        _log_view(request.user, patient, "PRESCRIPTIONS_VIEWED")
    else:
        return render(request, "records/prescriptions.html", {"needs_search": True})
    rows = Prescription.objects.filter(treatment__patient=patient).select_related("treatment", "treatment__doctor__user").prefetch_related("medicines")
    return render(request, "records/prescriptions.html", {"patient": patient, "prescriptions": rows})

@login_required
def reports(request):
    patient_id = request.GET.get("patient_id", "")
    if request.user.role == "PATIENT":
        patient = request.user.patient_profile
    elif patient_id:
        patient = get_object_or_404(Patient, patient_id=patient_id.strip().upper())
        if not can_access_patient(request.user, patient, "reports"):
            raise PermissionDenied("Patient report consent is required.")
        _log_view(request.user, patient, "REPORTS_VIEWED")
    else:
        return render(request, "records/reports.html", {"needs_search": True})
    return render(request, "records/reports.html", {"patient": patient, "reports": patient.reports.select_related("treatment", "uploaded_by")})

@login_required
def create_treatment(request):
    doctor, hospital = _provider_context(request.user)
    form = TreatmentCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        patient = get_object_or_404(Patient, patient_id=form.cleaned_data["patient_id"].strip().upper())
        if not can_access_patient(request.user, patient, "history"):
            raise PermissionDenied("Active history consent is required before recording treatment.")
        treatment = form.save(commit=False)
        treatment.patient = patient
        treatment.doctor = doctor
        treatment.hospital = hospital or (doctor.hospital if doctor else None)
        treatment.entered_by = request.user
        if treatment.disease_name.strip():
            treatment.disease, _ = Disease.objects.get_or_create(name=treatment.disease_name.strip())
        treatment.save()
        AccessLog.objects.create(patient=patient, actor=request.user, action="TREATMENT_CREATED", details=f"Treatment #{treatment.pk}")
        messages.success(request, "Treatment record saved.")
        return redirect(f"/records/history/?patient_id={patient.patient_id}")
    return render(request, "records/treatment_form.html", {"form": form})

@login_required
def create_prescription(request, treatment_id):
    doctor, hospital = _provider_context(request.user)
    treatment = get_object_or_404(Treatment.objects.select_related("patient"), pk=treatment_id)
    if not can_access_patient(request.user, treatment.patient, "prescriptions"):
        raise PermissionDenied("Patient prescription consent is required.")
    if treatment.doctor_id != (doctor.pk if doctor else None) and treatment.hospital_id != (hospital.pk if hospital else None):
        raise PermissionDenied("Only the treating provider can add a prescription.")
    medicine_form = MedicineEntryForm(request.POST or None)
    if request.method == "POST" and medicine_form.is_valid():
        prescription = Prescription.objects.create(treatment=treatment, notes=request.POST.get("notes", "")[:2000])
        medicine = medicine_form.save(commit=False)
        medicine.prescription = prescription
        medicine.save()
        AccessLog.objects.create(patient=treatment.patient, actor=request.user, action="PRESCRIPTION_CREATED", details=f"Prescription #{prescription.pk}")
        messages.success(request, "Prescription saved.")
        return redirect(f"/records/prescriptions/?patient_id={treatment.patient.patient_id}")
    return render(request, "records/prescription_form.html", {"form": medicine_form, "treatment": treatment})

@login_required
def upload_report(request, treatment_id):
    doctor, hospital = _provider_context(request.user)
    treatment = get_object_or_404(Treatment.objects.select_related("patient"), pk=treatment_id)
    if not can_access_patient(request.user, treatment.patient, "reports"):
        raise PermissionDenied("Patient report consent is required.")
    if treatment.doctor_id != (doctor.pk if doctor else None) and treatment.hospital_id != (hospital.pk if hospital else None):
        raise PermissionDenied("Only the treating provider can upload a report.")
    form = ReportUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.patient = treatment.patient
        report.treatment = treatment
        report.uploaded_by = request.user
        report.save()
        AccessLog.objects.create(patient=treatment.patient, actor=request.user, action="REPORT_UPLOADED", details=f"Report #{report.pk}")
        messages.success(request, "Report uploaded to private storage.")
        return redirect(f"/records/reports/?patient_id={treatment.patient.patient_id}")
    return render(request, "records/report_form.html", {"form": form, "treatment": treatment})

@login_required
def download_report(request, report_id):
    report = get_object_or_404(MedicalReport.objects.select_related("patient"), pk=report_id)
    if not can_access_patient(request.user, report.patient, "reports"):
        raise PermissionDenied("Patient report consent is required.")
    try:
        file_handle = report.file.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404
    _log_view(request.user, report.patient, "REPORT_DOWNLOADED", f"Report #{report.pk}")
    return FileResponse(file_handle, as_attachment=True, filename=os.path.basename(report.file.name))

@login_required
def appointments(request):
    if request.user.role == "PATIENT":
        rows = request.user.patient_profile.appointments.select_related("doctor__user", "hospital")
    elif request.user.role == "DOCTOR":
        doctor = get_object_or_404(Doctor, user=request.user, verified=True)
        if doctor.hospital_id and not doctor.hospital.approved:
            raise PermissionDenied
        rows = doctor.appointments.select_related("patient__user", "hospital")
    else:
        hospital, doctor = None, None
        if request.user.role == "HOSPITAL": hospital = get_object_or_404(Hospital, user=request.user, approved=True)
        if request.user.role == "STAFF": hospital = get_object_or_404(HospitalStaff, user=request.user, active=True, hospital__approved=True).hospital
        if hospital: rows = hospital.appointments.select_related("patient__user", "doctor__user")
        else: raise PermissionDenied
    return render(request, "records/appointments.html", {"appointments": rows})

@login_required
def create_appointment(request):
    is_patient = request.user.role == "PATIENT"
    if is_patient:
        doctor = hospital = None
        patient = request.user.patient_profile
    else:
        doctor, hospital = _provider_context(request.user)
        patient = None

    form = AppointmentCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        if is_patient:
            doctor = form.cleaned_data["doctor"]
            hospital = doctor.hospital
        else:
            patient = get_object_or_404(Patient, patient_id=form.cleaned_data["patient_id"].strip().upper())
            if not can_access_patient(request.user, patient, "history"):
                raise PermissionDenied("Active history consent is required to schedule care.")

        appointment = form.save(commit=False)
        appointment.patient = patient
        appointment.doctor = doctor
        appointment.hospital = hospital or (doctor.hospital if doctor else None)
        appointment.save()
        AccessLog.objects.create(patient=patient, actor=request.user, action="APPOINTMENT_CREATED", details=f"Appointment #{appointment.pk}")
        messages.success(request, "Appointment scheduled.")
        return redirect("records:appointments")
    return render(request, "records/appointment_form.html", {"form": form})

@login_required
def download_history_pdf(request):
    if request.user.role != "PATIENT":
        raise PermissionDenied
    from html import escape
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    patient = request.user.patient_profile
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=letter, title="Medical history")
    styles = getSampleStyleSheet()
    story = [Paragraph("Patient medical history", styles["Title"]), Paragraph(f"Patient ID: {escape(patient.patient_id)}", styles["Normal"]), Spacer(1, 12)]
    for item in patient.treatments.select_related("doctor__user", "hospital").prefetch_related("prescriptions__medicines", "reports"):
        story.extend([Paragraph(escape(str(item.treatment_date)), styles["Heading2"]), Paragraph(escape(item.disease_name or "Diagnosis"), styles["Heading3"]), Paragraph(escape(item.diagnosis), styles["BodyText"])])
        if item.doctor: story.append(Paragraph(escape(f"Doctor: {item.doctor.user.get_full_name()} — {item.doctor.specialization}"), styles["BodyText"]))
        if item.hospital: story.append(Paragraph(escape(f"Hospital: {item.hospital.name}"), styles["BodyText"]))
        if item.follow_up_date: story.append(Paragraph(escape(f"Follow-up: {item.follow_up_date}"), styles["BodyText"]))
        for prescription in item.prescriptions.all():
            story.append(Paragraph("Prescription", styles["Heading3"]))
            for medicine in prescription.medicines.all():
                detail = f"{medicine.medicine_name} — {medicine.dosage}; {medicine.frequency}; {medicine.duration}. {medicine.instructions}"
                story.append(Paragraph(escape(detail), styles["BodyText"]))
        for report in item.reports.all():
            story.append(Paragraph(escape(f"Report: {report.title} ({report.get_report_type_display()})"), styles["BodyText"]))
        story.append(Spacer(1, 8))
    document.build(story)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="medical-history.pdf"'
    return response
