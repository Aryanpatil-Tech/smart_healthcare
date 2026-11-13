from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from consent.models import ConsentRequest
from doctors.models import Doctor
from hospitals.models import Hospital
from medical_records.models import Appointment, MedicalReport, Treatment
from patients.models import Patient

User = get_user_model()


class HealthCardQrTests(TestCase):
    def test_patient_qr_endpoint_returns_svg(self):
        user = User.objects.create_user(
            username="qr_patient",
            email="qr-patient@example.test",
            password="StrongPass!234",
            role=User.Role.PATIENT,
        )
        Patient.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.get(reverse("health_cards:qr_image"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)


class ConsentAwareQrScanTests(TestCase):
    def setUp(self):
        self.provider_user = User.objects.create_user(
            username="scan_doctor",
            email="scan-doctor@example.test",
            password="StrongPass!234",
            role=User.Role.DOCTOR,
        )
        hospital_user = User.objects.create_user(
            username="scan_hospital",
            email="scan-hospital@example.test",
            password="StrongPass!234",
            role=User.Role.HOSPITAL,
        )
        hospital = Hospital.objects.create(
            user=hospital_user,
            name="Scan Test Clinic",
            registration_number="SCAN-HOSP-1",
            address="Example Road",
            approved=True,
        )
        self.doctor = Doctor.objects.create(
            user=self.provider_user,
            qualification="MD",
            specialization="Family Medicine",
            registration_number="SCAN-MED-1",
            hospital=hospital,
            verified=True,
        )
        patient_user = User.objects.create_user(
            username="scan_patient",
            email="scan-patient@example.test",
            password="StrongPass!234",
            role=User.Role.PATIENT,
        )
        self.patient = Patient.objects.create(user=patient_user)
        self.treatment = Treatment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            hospital=hospital,
            entered_by=self.provider_user,
            disease_name="Synthetic scan diagnosis",
            diagnosis="Synthetic scan diagnosis details",
            treatment_date=timezone.localdate(),
        )
        MedicalReport.objects.create(
            patient=self.patient,
            treatment=self.treatment,
            title="Synthetic scan report",
            file="reports/synthetic.pdf",
            uploaded_by=self.provider_user,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            hospital=hospital,
            scheduled_for=timezone.now() + timedelta(days=1),
            follow_up_notes="Synthetic appointment details",
        )
        self.client.force_login(self.provider_user)

    def test_scan_without_consent_shows_identity_only(self):
        response = self.client.get(reverse("health_cards:scan", args=[self.patient.lookup_token]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.patient_id)
        self.assertNotContains(response, "Synthetic scan diagnosis details")
        self.assertNotContains(response, "Synthetic scan report")
        self.assertNotContains(response, "Synthetic appointment details")

    def test_scan_shows_only_approved_categories(self):
        ConsentRequest.objects.create(
            patient=self.patient,
            requester=self.provider_user,
            purpose="Synthetic test access",
            history_access=True,
            reports_access=True,
            appointments_access=True,
            status=ConsentRequest.Status.APPROVED,
            expires_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(reverse("health_cards:scan", args=[self.patient.lookup_token]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Synthetic scan diagnosis details")
        self.assertContains(response, "Synthetic scan report")
        self.assertContains(response, "Synthetic appointment details")
        self.assertNotContains(response, "APPROVED · PRESCRIPTIONS")