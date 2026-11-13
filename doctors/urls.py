from django.urls import path
from . import views
app_name = "doctors"
urlpatterns = [path("patients/search/", views.search_patient, name="search_patient"), path("profile/", views.profile, name="profile"), path("profile/photo/", views.photo, name="photo")]
