from django.urls import path
from . import views
app_name = "consent"
urlpatterns = [
    path("request/", views.request_access, name="request"),
    path("manage/", views.manage_consent, name="manage"),
    path("<int:consent_id>/revoke/", views.revoke_consent, name="revoke"),
]
