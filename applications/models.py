from django.db import models
from django.conf import settings
from django.utils import timezone


class Student(models.Model):
    GENDER_MALE = 'MALE'
    GENDER_FEMALE = 'FEMALE'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    ]

    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year / Post-Grad'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=30, unique=True, help_text="Roll Number / Registration Number")
    name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    course = models.CharField(max_length=100)
    year = models.PositiveIntegerField(choices=YEAR_CHOICES, default=1)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=15)
    merit_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=75.0,
        help_text="Merit percentage / score for priority allocation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.student_id} - {self.name} ({self.get_gender_display()})"


class ApplicationPeriod(models.Model):
    academic_year = models.CharField(max_length=20, default='2026-2027')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-start_date']

    @property
    def is_currently_open(self):
        today = timezone.now().date()
        return self.is_active and (self.start_date <= today <= self.end_date)

    def __str__(self):
        status_str = "OPEN" if self.is_currently_open else "CLOSED"
        return f"{self.academic_year} ({status_str}: {self.start_date} to {self.end_date})"


class Application(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_WAITLISTED = 'WAITLISTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WAITLISTED, 'Waitlisted'),
    ]

    ROOM_TYPE_CHOICES = [
        ('SINGLE', 'Single Room (1 Bed)'),
        ('DOUBLE', 'Double Sharing (2 Beds)'),
        ('TRIPLE', 'Triple Sharing (3 Beds)'),
        ('FOUR_SHARING', 'Four Sharing (4 Beds)'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    academic_year = models.CharField(max_length=20)
    preferred_room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    remarks = models.TextField(blank=True, default='')
    priority_score = models.IntegerField(default=0, help_text="Calculated priority score for room allotment")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority_score', 'application_date']

    def __str__(self):
        return f"App #{self.pk} - {self.student.name} ({self.academic_year}) - {self.get_status_display()}"
