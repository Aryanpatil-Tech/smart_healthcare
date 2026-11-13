from django import forms
from .models import ConsentRequest

class ConsentRequestForm(forms.ModelForm):
    class Meta:
        model = ConsentRequest
        fields = ("history_access", "prescriptions_access", "reports_access", "appointments_access", "purpose")
        widgets = {"purpose": forms.TextInput(attrs={"placeholder": "e.g. Consultation for today's visit"})}

class ConsentDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    duration_days = forms.IntegerField(min_value=1, max_value=30, initial=7, required=False, help_text="Approval duration, up to 30 days.")
