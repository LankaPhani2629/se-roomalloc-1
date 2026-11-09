from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from applications.models import Student, Application
from hostels.models import Room


class Allocation(models.Model):
    STATUS_PENDING_PAYMENT = 'PENDING_PAYMENT'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_VACATED = 'VACATED'
    STATUS_EXPIRED = 'EXPIRED'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Pending Fee Payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_VACATED, 'Vacated'),
        (STATUS_EXPIRED, 'Expired (Unpaid)'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    application = models.OneToOneField(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocation'
    )
    academic_year = models.CharField(max_length=20, default='2026-2027')
    allocation_date = models.DateField(default=timezone.now)
    check_in_date = models.DateField(null=True, blank=True)
    vacate_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(help_text="Deadline for fee payment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
    is_active = models.BooleanField(default=True, help_text="Designates if this is student's current active allotment")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-allocation_date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=models.Q(is_active=True),
                name='unique_active_allotment_per_student'
            )
        ]

    def clean(self):
        # Business rule 1: Boys and girls are allotted only to their respective hostels
        if self.student and self.room:
            if self.student.gender == Student.GENDER_MALE and self.room.hostel.hostel_type != 'BOYS':
                raise ValidationError("Male students can only be allotted to Boys Hostels.")
            if self.student.gender == Student.GENDER_FEMALE and self.room.hostel.hostel_type != 'GIRLS':
                raise ValidationError("Female students can only be allotted to Girls Hostels.")

        # Business rule 2: Room cannot exceed capacity
        if self.room and self.pk is None and self.is_active:
            if self.room.occupied_count >= self.room.capacity:
                raise ValidationError(f"Room {self.room.room_no} in {self.room.hostel.name} has already reached its capacity ({self.room.capacity}).")

    def __str__(self):
        return f"Allocation: {self.student.name} -> {self.room} ({self.get_status_display()})"


class RoomChangeRequest(models.Model):
    TYPE_CHANGE = 'CHANGE'
    TYPE_VACATE = 'VACATE'
    TYPE_CHOICES = [
        (TYPE_CHANGE, 'Room Change Request'),
        (TYPE_VACATE, 'Room Vacating Request'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='room_change_requests')
    current_allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name='change_requests')
    request_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_CHANGE)
    preferred_room_type = models.CharField(max_length=20, blank=True)
    target_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_change_requests'
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    warden_remarks = models.TextField(blank=True, default='')
    actioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actioned_room_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    actioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} by {self.student.name} - {self.get_status_display()}"


class AllocationRule(models.Model):
    GENDER_ALL = 'ALL'
    GENDER_MALE = 'MALE'
    GENDER_FEMALE = 'FEMALE'
    GENDER_CHOICES = [
        (GENDER_ALL, 'All Genders'),
        (GENDER_MALE, 'Male Only'),
        (GENDER_FEMALE, 'Female Only'),
    ]

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_ALL)
    year_of_study = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank to apply to all years")
    room_type = models.CharField(max_length=20, blank=True, help_text="Target room type preference, or blank for all")
    priority_order = models.PositiveIntegerField(default=1, help_text="Lower number = higher priority order")
    merit_weight = models.PositiveIntegerField(default=10, help_text="Weight points added to merit score")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority_order', 'id']

    def __str__(self):
        return f"Rule: {self.name} (Priority {self.priority_order})"
