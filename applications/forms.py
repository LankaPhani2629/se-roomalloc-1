from django import forms
from .models import Student, Application, ApplicationPeriod


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone', 'email', 'address', 'guardian_name', 'guardian_phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RoomApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['preferred_room_type']
        widgets = {
            'preferred_room_type': forms.Select(attrs={'class': 'form-select'}),
        }


class ApplicationPeriodForm(forms.ModelForm):
    class Meta:
        model = ApplicationPeriod
        fields = ['academic_year', 'start_date', 'end_date', 'is_active', 'description']
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026-2027'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description'}),
        }


class ApplicationReviewForm(forms.Form):
    STATUS_CHOICES = [
        (Application.STATUS_APPROVED, 'Approve Application'),
        (Application.STATUS_WAITLISTED, 'Waitlist Application'),
        (Application.STATUS_REJECTED, 'Reject Application'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Warden remarks or reason...'})
    )

