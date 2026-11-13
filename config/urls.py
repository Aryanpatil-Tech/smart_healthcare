from django.contrib import admin
from django.urls import include, path
from dashboard import views as dashboard_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_views.home, name="home"),
    path("about/", dashboard_views.about, name="about"),
    path("accounts/", include("accounts.urls")),
    path("patient/", include("patients.urls")),
    path("doctor/", include("doctors.urls")),
    path("hospital/", include("hospitals.urls")),
    path("records/", include("medical_records.urls")),
    path("card/", include("health_cards.urls")),
    path("consent/", include("consent.urls")),
    path("dashboard/", include("dashboard.urls")),
]
