from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/doctor/", views.login_view, {"expected_role": "DOCTOR"}, name="doctor_login"),
    path("login/hospital/", views.login_view, {"expected_role": "HOSPITAL"}, name="hospital_login"),
    path("login/admin/", views.login_view, {"expected_role": "ADMIN"}, name="admin_login"),
    path("register/patient/", views.register_patient, name="register_patient"),
    path("register/doctor/", views.register_doctor, name="register_doctor"),
    path("register/hospital/", views.register_hospital, name="register_hospital"),
    path("logout/", views.logout_view, name="logout"),
]
