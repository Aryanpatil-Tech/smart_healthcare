from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from doctors.models import Doctor
from hospitals.models import Hospital
from patients.models import Patient
from .models import ConsentRequest
from .services import can_access_patient

User = get_user_model()

class ConsentAccessTests(TestCase):
    def setUp(self):
        self.hospital_user = User.objects.create_user(username="test_hospital", email="hospital@example.test", password="StrongPass!234", role=User.Role.HOSPITAL)
        self.hospital = Hospital.objects.create(user=self.hospital_user, name="Synthetic Clinic", registration_number="TEST-HOSP-1", address="Example", approved=True)
        self.doctor_user = User.objects.create_user(username="test_doctor", email="doctor@example.test", password="StrongPass!234", role=User.Role.DOCTOR)
        self.doctor = Doctor.objects.create(user=self.doctor_user, qualification="MD", specialization="Family Medicine", registration_number="TEST-MED-1", hospital=self.hospital, verified=True)
        self.patient_user = User.objects.create_user(username="test_patient", email="patient@example.test", password="StrongPass!234", role=User.Role.PATIENT)
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_patient_can_access_own_records(self):
        self.assertTrue(can_access_patient(self.patient_user, self.patient, "history"))

    def test_provider_needs_scoped_active_consent(self):
        self.assertFalse(can_access_patient(self.doctor_user, self.patient, "history"))
        ConsentRequest.objects.create(patient=self.patient, requester=self.doctor_user, history_access=True, purpose="Synthetic test", status=ConsentRequest.Status.APPROVED, expires_at=timezone.now() + timedelta(days=1))
        self.assertTrue(can_access_patient(self.doctor_user, self.patient, "history"))
        self.assertFalse(can_access_patient(self.doctor_user, self.patient, "reports"))

    def test_expired_consent_is_inactive(self):
        ConsentRequest.objects.create(patient=self.patient, requester=self.doctor_user, reports_access=True, purpose="Synthetic test", status=ConsentRequest.Status.APPROVED, expires_at=timezone.now() - timedelta(seconds=1))
        self.assertFalse(can_access_patient(self.doctor_user, self.patient, "reports"))

    def test_history_endpoint_denies_provider_without_consent(self):
        self.client.force_login(self.doctor_user)
        response = self.client.get(reverse("records:history"), {"patient_id": self.patient.patient_id})
        self.assertEqual(response.status_code, 403)

    def test_history_endpoint_logs_provider_access(self):
        ConsentRequest.objects.create(patient=self.patient, requester=self.doctor_user, history_access=True, purpose="Synthetic test", status=ConsentRequest.Status.APPROVED, expires_at=timezone.now() + timedelta(days=1))
        self.client.force_login(self.doctor_user)
        response = self.client.get(reverse("records:history"), {"patient_id": self.patient.patient_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.patient.access_logs.filter(actor=self.doctor_user, action="MEDICAL_HISTORY_VIEWED").exists())
