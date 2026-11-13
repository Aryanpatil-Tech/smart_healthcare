from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from doctors.models import Doctor
from hospitals.models import Hospital
from medical_records.models import Appointment
from patients.models import Patient

User = get_user_model()


class PatientAppointmentTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="booking_patient",
            email="booking-patient@example.test",
            password="StrongPass!234",
            role=User.Role.PATIENT,
        )
        self.patient = Patient.objects.create(user=self.patient_user)
        hospital_user = User.objects.create_user(
            username="booking_hospital",
            email="booking-hospital@example.test",
            password="StrongPass!234",
            role=User.Role.HOSPITAL,
        )
        hospital = Hospital.objects.create(
            user=hospital_user,
            name="Booking Clinic",
            registration_number="BOOKING-HOSP-1",
            address="Example Road",
            approved=True,
        )
        doctor_user = User.objects.create_user(
            username="booking_doctor",
            email="booking-doctor@example.test",
            password="StrongPass!234",
            role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=doctor_user,
            qualification="MD",
            specialization="Family Medicine",
            registration_number="BOOKING-MED-1",
            hospital=hospital,
            verified=True,
        )

    def test_patient_can_open_booking_form(self):
        self.client.force_login(self.patient_user)

        response = self.client.get(reverse("records:create_appointment"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book an appointment")

    def test_patient_booking_is_saved_to_their_own_profile(self):
        self.client.force_login(self.patient_user)
        scheduled_for = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")

        response = self.client.post(
            reverse("records:create_appointment"),
            {
                "doctor": self.doctor.pk,
                "scheduled_for": scheduled_for,
                "follow_up_notes": "Synthetic test booking",
            },
        )

        self.assertRedirects(response, reverse("records:appointments"))
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)