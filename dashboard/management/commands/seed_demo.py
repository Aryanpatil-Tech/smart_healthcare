from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from consent.models import ConsentRequest
from doctors.models import Doctor
from hospitals.models import Hospital
from medical_records.models import Disease, Prescription, PrescriptionMedicine, Treatment
from patients.models import Patient

DEMO_PASSWORD = "DemoPass!234"

class Command(BaseCommand):
    help = "Create synthetic, local-development-only CareVault demo accounts and records."

    def handle(self, *args, **options):
        def account(username, email, first, last, role):
            user, _ = User.objects.get_or_create(username=username, defaults={"email": email, "first_name": first, "last_name": last, "role": role})
            user.email, user.first_name, user.last_name, user.role = email, first, last, role
            user.is_active = True
            user.set_password(DEMO_PASSWORD)
            user.save()
            return user

        hospital_user = account("demo_hospital", "hospital@example.test", "Demo", "Hospital", User.Role.HOSPITAL)
        hospital, _ = Hospital.objects.update_or_create(user=hospital_user, defaults={"name": "Northstar Community Clinic", "registration_number": "DEMO-HOSP-001", "address": "100 Example Avenue, Sample City", "phone": "+1 555 010 2000", "email": hospital_user.email, "approved": True})
        doctor_user = account("demo_doctor", "doctor@example.test", "Avery", "Rivera", User.Role.DOCTOR)
        doctor, _ = Doctor.objects.update_or_create(user=doctor_user, defaults={"qualification": "MD (Synthetic Sample)", "specialization": "Family Medicine", "registration_number": "DEMO-MED-001", "experience_years": 8, "hospital": hospital, "verified": True})
        patient_user = account("demo_patient", "patient@example.test", "Jordan", "Lee", User.Role.PATIENT)
        patient, _ = Patient.objects.get_or_create(user=patient_user, defaults={"date_of_birth": date(1990, 5, 14), "gender": Patient.Gender.UNSPECIFIED, "blood_group": Patient.BloodGroup.UNKNOWN, "address": "42 Example Road, Sample City", "emergency_contact_name": "Taylor Lee", "emergency_contact_phone": "+1 555 010 4040"})
        disease, _ = Disease.objects.get_or_create(name="Seasonal allergic rhinitis", defaults={"description": "Synthetic example diagnosis for software testing."})
        treatment, _ = Treatment.objects.get_or_create(patient=patient, doctor=doctor, hospital=hospital, disease=disease, treatment_date=date.today() - timedelta(days=14), defaults={"entered_by": doctor_user, "disease_name": disease.name, "symptoms": "Synthetic example: sneezing and itchy eyes.", "diagnosis": "Synthetic sample diagnosis only.", "treatment_details": "Example care plan; not medical advice.", "follow_up_date": date.today() + timedelta(days=14), "status": Treatment.Status.FOLLOW_UP})
        prescription, _ = Prescription.objects.get_or_create(treatment=treatment, defaults={"notes": "Synthetic sample prescription. Not for clinical use."})
        PrescriptionMedicine.objects.get_or_create(prescription=prescription, medicine_name="Example medicine (not real) ", defaults={"dosage": "As entered by sample clinician", "frequency": "Example only", "duration": "Example only", "instructions": "Synthetic test data; do not use."})
        demo_consent, _ = ConsentRequest.objects.get_or_create(patient=patient, requester=doctor_user, purpose="Synthetic demo access", defaults={"history_access": True, "prescriptions_access": True, "reports_access": True, "appointments_access": True, "status": ConsentRequest.Status.APPROVED, "expires_at": timezone.now() + timedelta(days=7), "responded_at": timezone.now()})
        if demo_consent.status == ConsentRequest.Status.APPROVED and demo_consent.expires_at and demo_consent.expires_at > timezone.now() and not demo_consent.appointments_access:
            demo_consent.appointments_access = True
            demo_consent.save(update_fields=["appointments_access"])
        self.stdout.write(self.style.SUCCESS("Synthetic demo data is ready (local development only):"))
        self.stdout.write("  demo_patient / DemoPass!234")
        self.stdout.write("  demo_doctor / DemoPass!234 (verified; demo patient consent active)")
        self.stdout.write("  demo_hospital / DemoPass!234 (approved)")
