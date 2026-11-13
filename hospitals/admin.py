from django.contrib import admin
from .models import Hospital, HospitalStaff

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_number", "approved", "created_at")
    list_filter = ("approved",)
    search_fields = ("name", "registration_number", "user__email")
    actions = ["approve_selected"]
    @admin.action(description="Approve selected hospitals")
    def approve_selected(self, request, queryset): queryset.update(approved=True)

admin.site.register(HospitalStaff)
