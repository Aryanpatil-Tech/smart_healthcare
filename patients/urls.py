from django.urls import path
from . import views
app_name = "patients"
urlpatterns = [path("profile/", views.profile, name="profile"), path("access-logs/", views.access_logs, name="access_logs")]
