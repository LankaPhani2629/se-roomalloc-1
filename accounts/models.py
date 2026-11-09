from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = 'STUDENT'
    ROLE_WARDEN = 'WARDEN'
    ROLE_ADMIN = 'ADMIN'
    ROLE_ACCOUNTANT = 'ACCOUNTANT'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_WARDEN, 'Warden'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_ACCOUNTANT, 'Accountant'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        help_text='Designates the role for role-based access control.'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)

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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
