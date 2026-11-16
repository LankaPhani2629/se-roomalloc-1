from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = 'STUDENT'
    ROLE_WARDEN = 'WARDEN'
    ROLE_ADMIN = 'ADMIN'
    ROLE_ACCOUNTANT = 'ACCOUNTANT'
    ROLE_FACULTY = 'FACULTY'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_WARDEN, 'Warden'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_ACCOUNTANT, 'Accountant'),
        (ROLE_FACULTY, 'Faculty/HOD'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        help_text='Designates the role for role-based access control.'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_first_login = models.BooleanField(
        default=False,
        help_text='Flag to force staff users to change password on first login.'
    )
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text='Tracks consecutive failed login attempts for brute-force lock.'
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp until which account is locked after 5 failed attempts.'
    )

    @property
    def is_locked(self):
        from django.utils import timezone
        return bool(self.locked_until and self.locked_until > timezone.now())

    @property
    def has_2fa_enabled(self):
        """Check if user has an active confirmed TOTP device."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            return TOTPDevice.objects.filter(user=self, confirmed=True).exists()
        except Exception:
            return False

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_warden(self):
        return self.role == self.ROLE_WARDEN

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_accountant(self):
        return self.role == self.ROLE_ACCOUNTANT

    @property
    def is_faculty(self):
        return self.role == self.ROLE_FACULTY

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class FacultyProfile(models.Model):
    """
    Profile for Faculty and Head of Department (HOD) users.
    Faculty verify student applications belonging to their department.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='faculty_profile'
    )
    employee_id = models.CharField(max_length=50, unique=True, help_text="Faculty Employee ID")
    name = models.CharField(max_length=150)
    department = models.CharField(max_length=100, help_text="e.g. Computer Science, Biotechnology, etc.")
    designation = models.CharField(max_length=100, default='Assistant Professor', help_text="e.g. Assistant Professor, Professor & HOD")
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.name} - {self.designation} ({self.department})"


class WardenProfile(models.Model):
    """
    Profile for Warden users assigned to a specific hostel.
    Warden views are strictly scoped to their assigned hostel.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='warden_profile'
    )
    employee_id = models.CharField(max_length=50, unique=True, help_text="Warden Employee ID")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    assigned_hostel = models.ForeignKey(
        'hostels.Hostel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warden_profiles',
        help_text="Hostel complex assigned to this warden"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        hostel_name = self.assigned_hostel.name if self.assigned_hostel else "Unassigned"
        return f"{self.name} - Warden ({hostel_name})"
