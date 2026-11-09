from django import forms
from django.utils import timezone
from .models import FeeStructure, FeePayment
from allocations.models import Allocation


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['room_type', 'academic_year', 'amount', 'due_days', 'description']
        widgets = {
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026-2027'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1.00', 'placeholder': 'Fee amount in INR'}),
            'due_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description / notes'}),
        }


class RecordPaymentForm(forms.ModelForm):
    allocation = forms.ModelChoiceField(
        queryset=Allocation.objects.filter(is_active=True).select_related('student', 'room', 'room__hostel'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Student Allocation"
    )

    class Meta:
        model = FeePayment
        fields = ['allocation', 'amount', 'payment_mode', 'transaction_id', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1.00'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique Transaction ID / Ref'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional payment notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prefill default transaction ID
        if not self.initial.get('transaction_id'):
            self.initial['transaction_id'] = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
