from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class HealthUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Healthcare role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Healthcare role", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
