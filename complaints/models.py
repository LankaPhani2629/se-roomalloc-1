from django.db import models
from django.conf import settings
from applications.models import Student
from hostels.models import Room


class Complaint(models.Model):
    CAT_MAINTENANCE = 'MAINTENANCE'
    CAT_ELECTRICAL = 'ELECTRICAL'
    CAT_PLUMBING = 'PLUMBING'
    CAT_CLEANLINESS = 'CLEANLINESS'
    CAT_DISCIPLINE = 'DISCIPLINE'
    CAT_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CAT_MAINTENANCE, 'Civil / Room Maintenance'),
        (CAT_ELECTRICAL, 'Electrical (Fan, Light, Switch)'),
        (CAT_PLUMBING, 'Plumbing / Washroom Water'),
        (CAT_CLEANLINESS, 'Housekeeping & Cleanliness'),
        (CAT_DISCIPLINE, 'Discipline / Noise'),
        (CAT_OTHER, 'Other Issue'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='complaints')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CAT_MAINTENANCE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    warden_remarks = models.TextField(blank=True, default='')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_complaints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint #{self.pk}: {self.title} ({self.get_status_display()})"
