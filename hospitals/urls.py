from django.urls import path
from . import views
app_name = "hospitals"
urlpatterns = [path("staff/", views.manage_staff, name="staff")]
