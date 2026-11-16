from django.db import models
from django.conf import settings
from django.utils import timezone
from applications.models import Student
from hostels.models import Room


class MaintenanceStaff(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    specialization = models.CharField(
        max_length=100,
        help_text="e.g. Electrician, Plumber, Carpenter, Housekeeping, Internet Support"
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.specialization})"


class MaintenanceRequest(models.Model):
    CAT_ELECTRICITY = 'ELECTRICITY'
    CAT_WATER = 'WATER'
    CAT_FURNITURE = 'FURNITURE'
    CAT_CLEANING = 'CLEANING'
    CAT_INTERNET = 'INTERNET'
    CAT_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CAT_ELECTRICITY, 'Electricity / Power Outage'),
        (CAT_WATER, 'Plumbing & Water Supply'),
        (CAT_FURNITURE, 'Furniture & Bed Fixtures'),
        (CAT_CLEANING, 'Sanitation & Cleaning'),
        (CAT_INTERNET, 'Wi-Fi & LAN Connectivity'),
        (CAT_OTHER, 'Other Maintenance Issue'),
    ]

    PRIO_LOW = 'LOW'
    PRIO_MEDIUM = 'MEDIUM'
    PRIO_HIGH = 'HIGH'
    PRIO_EMERGENCY = 'EMERGENCY'

    PRIORITY_CHOICES = [
        (PRIO_LOW, 'Low Priority'),
        (PRIO_MEDIUM, 'Medium Priority'),
        (PRIO_HIGH, 'High Priority'),
        (PRIO_EMERGENCY, 'Emergency / Urgent'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_REOPENED = 'REOPENED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open Ticket'),
        (STATUS_ASSIGNED, 'Assigned to Staff'),
        (STATUS_IN_PROGRESS, 'Work In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed & Verified'),
        (STATUS_REOPENED, 'Reopened by Student'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='maintenance_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenance_requests')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(help_text="Detailed description of the maintenance issue.")
    photo = models.ImageField(upload_to='maintenance_photos/', blank=True, null=True, help_text="Optional photo of the issue")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIO_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

    assigned_staff = models.ForeignKey(
        MaintenanceStaff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    warden_notes = models.TextField(blank=True, default='')
    resolution_notes = models.TextField(blank=True, default='')
    
    # 1 to 5 star rating given by the student upon resolution
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1 to 5 star rating by student")
    student_feedback = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def resolution_duration_hours(self):
        """Hours taken from creation to resolution."""
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600.0, 1)
        return None

    def mark_resolved(self, notes=""):
        self.status = self.STATUS_RESOLVED
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolution_notes'])

    def __str__(self):
        return f"Ticket #{self.pk}: {self.get_category_display()} - Room {self.room.room_no} ({self.get_status_display()})"
