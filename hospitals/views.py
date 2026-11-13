from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from .models import Hospital, HospitalStaff
User = get_user_model()

@login_required
def manage_staff(request):
    if request.user.role != "HOSPITAL":
        raise PermissionDenied
    hospital = request.user.hospital_profile
    if not hospital.approved:
        raise PermissionDenied("Hospital approval is required to manage staff.")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        staff_user = User.objects.filter(username=username, role=User.Role.STAFF).first()
        if not staff_user:
            error = "Create a staff login account through your administrator before linking it here."
        else:
            _, created = HospitalStaff.objects.get_or_create(user=staff_user, hospital=hospital, defaults={"active": True})
            if created:
                messages.success(request, "Staff member linked to this hospital.")
                return redirect("hospitals:staff")
            error = "This staff member is already linked."
    return render(request, "hospitals/staff.html", {"hospital": hospital, "staff": hospital.staff.select_related("user"), "error": error})
