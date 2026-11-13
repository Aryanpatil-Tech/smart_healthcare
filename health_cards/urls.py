from django.urls import path
from . import views
app_name = "health_cards"
urlpatterns = [path("", views.card, name="card"), path("qr.svg", views.qr_image, name="qr_image"), path("verify/<uuid:token>/", views.scan, name="scan")]
