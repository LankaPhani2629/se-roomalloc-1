from django import forms
from .models import Complaint


class ComplaintSubmitForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'title', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description of the complaint or maintenance issue...'}),
        }


class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'warden_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'warden_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Action taken or explanation for student...'}),
        }

