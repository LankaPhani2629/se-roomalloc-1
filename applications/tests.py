from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from applications.models import Student, Application, ApplicationPeriod

User = get_user_model()


class ApplicationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"

        # Student user and profile
        self.student_user = User.objects.create_user(
            username="app_student",
            email="appstudent@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="ROLL-APP-01",
            name="Alice Applicant",
            gender=Student.GENDER_FEMALE,
            course="B.Sc Biotechnology",
            year=2,
            phone="9123456789",
            email="appstudent@college.edu",
            address="789 Avenue",
            guardian_name="Guardian Alice",
            guardian_phone="9123456780",
            merit_score=92.5
        )

        # Warden
        self.warden_user = User.objects.create_user(
            username="app_warden",
            email="warden@college.edu",
            password=self.password,
            role=User.ROLE_WARDEN
        )

    def test_application_submission_open_period(self):
        """Test application submission while application window is open."""
        ApplicationPeriod.objects.create(
            academic_year="2026-2027",
            start_date=timezone.now().date() - timedelta(days=2),
            end_date=timezone.now().date() + timedelta(days=10),
            is_active=True
        )

        self.client.login(username="app_student", password=self.password)
        response = self.client.post(reverse('apply_room'), {
            'preferred_room_type': 'DOUBLE'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('student_application_status'))

        app = Application.objects.filter(student=self.student).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.preferred_room_type, 'DOUBLE')
        self.assertEqual(app.status, Application.STATUS_PENDING)

    def test_application_submission_closed_period(self):
        """Test application cannot be submitted when application window is closed."""
        # No active open period
        ApplicationPeriod.objects.create(
            academic_year="2025-2026",
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() - timedelta(days=10),
            is_active=True
        )

        self.client.login(username="app_student", password=self.password)
        response = self.client.get(reverse('apply_room'))
        self.assertContains(response, "Hostel Application Period Closed")

        # Post should not create an application
        post_response = self.client.post(reverse('apply_room'), {
            'preferred_room_type': 'SINGLE'
        })
        self.assertContains(post_response, "Hostel Application Period Closed")
        self.assertEqual(Application.objects.count(), 0)

    def test_warden_approval_and_remarks(self):
        """Test warden reviewing and approving an application."""
        app = Application.objects.create(
            student=self.student,
            academic_year="2026-2027",
            preferred_room_type="DOUBLE",
            status=Application.STATUS_PENDING
        )

        self.client.login(username="app_warden", password=self.password)
        response = self.client.post(reverse('warden_application_review', kwargs={'pk': app.pk}), {
            'status': Application.STATUS_APPROVED,
            'remarks': 'Verified merit score and academic record.'
        })
        self.assertEqual(response.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, Application.STATUS_APPROVED)
        self.assertEqual(app.remarks, 'Verified merit score and academic record.')
        self.assertEqual(app.reviewed_by, self.warden_user)
