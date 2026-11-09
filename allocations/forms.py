from django import forms
from .models import AllocationRule, RoomChangeRequest, Allocation
from hostels.models import Room, Hostel
from applications.models import Student


class AllocationRuleForm(forms.ModelForm):
    class Meta:
        model = AllocationRule
        fields = ['name', 'gender', 'year_of_study', 'room_type', 'priority_order', 'merit_weight', 'is_active', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1st Year Priority Rule'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year (1-5) or leave blank'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}, choices=[('', '-- Any Room Type --')] + Room.ROOM_TYPE_CHOICES),
            'priority_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'merit_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ManualAllocationForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(allocations__is_active=False).distinct() | Student.objects.filter(allocations__isnull=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Student (without active allotment)"
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(status=Room.STATUS_AVAILABLE),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Available Room"
    )
    due_days = forms.IntegerField(
        initial=7,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Fee Payment Due Days"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude students who already have an active allocation
        active_student_ids = Allocation.objects.filter(is_active=True).values_list('student_id', flat=True)
        self.fields['student'].queryset = Student.objects.exclude(id__in=active_student_ids)


class RoomChangeRequestForm(forms.ModelForm):
    class Meta:
        model = RoomChangeRequest
        fields = ['request_type', 'preferred_room_type', 'reason']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_room_type': forms.Select(attrs={'class': 'form-select'}, choices=[('', '-- Any / Not Applicable --')] + Room.ROOM_TYPE_CHOICES),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed explanation for room change or vacating...'}),
        }


class ProcessRoomRequestForm(forms.Form):
    DECISION_CHOICES = [
        ('APPROVED', 'Approve Request'),
        ('REJECTED', 'Reject Request'),
    ]
    decision = forms.ChoiceField(choices=DECISION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    target_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(status=Room.STATUS_AVAILABLE),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="-- Select Destination Room (Required if Room Change) --"
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Warden remarks / instructions...'})
    )
