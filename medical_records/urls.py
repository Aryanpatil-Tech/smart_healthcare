from django.urls import path
from . import views
app_name = "records"
urlpatterns = [
    path("history/", views.history, name="history"),
    path("prescriptions/", views.prescriptions, name="prescriptions"),
    path("reports/", views.reports, name="reports"),
    path("reports/<int:report_id>/download/", views.download_report, name="download_report"),
    path("treatments/new/", views.create_treatment, name="create_treatment"),
    path("treatments/<int:treatment_id>/prescribe/", views.create_prescription, name="create_prescription"),
    path("treatments/<int:treatment_id>/reports/upload/", views.upload_report, name="upload_report"),
    path("appointments/", views.appointments, name="appointments"),
    path("appointments/new/", views.create_appointment, name="create_appointment"),
    path("history/download/", views.download_history_pdf, name="download_history_pdf"),
]
