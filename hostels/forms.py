from django import forms
from .models import Hostel, Room
from accounts.models import User


class HostelForm(forms.ModelForm):
    warden = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.ROLE_WARDEN),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="-- Select Warden (Optional) --"
    )

    class Meta:
        model = Hostel
        fields = ['name', 'hostel_type', 'warden', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Brahmaputra Boys Hostel'}),
            'hostel_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hostel description, facilities, etc.'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['hostel', 'floor_no', 'room_no', 'capacity', 'room_type', 'status']
        widgets = {
            'hostel': forms.Select(attrs={'class': 'form-select'}),
            'floor_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'room_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101, 204-A'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        capacity = cleaned_data.get('capacity')
        if self.instance and self.instance.pk:
            if capacity and capacity < self.instance.occupied_count:
                raise forms.ValidationError(
                    f"Capacity ({capacity}) cannot be lower than the current occupied count ({self.instance.occupied_count})."
                )
        return cleaned_data

