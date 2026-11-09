from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from applications.models import Student

User = get_user_model()


class AccountsSecurityAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"

        # Admin user
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@college.edu",
            password=self.password,
            role=User.ROLE_ADMIN
        )

        # Student user and profile
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="ROLL-TEST-01",
            name="Test Student",
            gender=Student.GENDER_MALE,
            course="B.Tech Computer Science",
            year=1,
            phone="9876543210",
            email="student@college.edu",
            address="123 Test St",
            guardian_name="Guardian Name",
            guardian_phone="9876543211",
            merit_score=85.0
        )

        # Warden user
        self.warden_user = User.objects.create_user(
            username="warden_user",
            email="warden@college.edu",
            password=self.password,
            role=User.ROLE_WARDEN
        )

    def test_valid_login(self):
        """Test valid user login redirects to dashboard redirect."""
        response = self.client.post(reverse('login'), {
            'username': 'student_user',
            'password': self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard_redirect'))

    def test_invalid_login(self):
        """Test invalid login credentials fails with error message."""
        response = self.client.post(reverse('login'), {
            'username': 'student_user',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_password_is_hashed(self):
        """Verify passwords are never stored in plain text."""
        self.assertNotEqual(self.student_user.password, self.password)
        self.assertTrue(self.student_user.check_password(self.password))

    def test_unauthorized_access_denied(self):
        """Test student cannot access administrator pages (PermissionDenied 403)."""
        self.client.login(username='student_user', password=self.password)
        # Attempt to access admin dashboard
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)

        # Attempt to access hostel create page
        response = self.client.get(reverse('hostel_create'))
        self.assertEqual(response.status_code, 403)

    def test_role_based_dashboard_redirect(self):
        """Test each role redirects to its specific dashboard."""
        # 1. Student
        self.client.login(username='student_user', password=self.password)
        res = self.client.get(reverse('dashboard_redirect'), follow=True)
        self.assertRedirects(res, reverse('student_dashboard'))
        self.client.logout()

        # 2. Warden
        self.client.login(username='warden_user', password=self.password)
        res = self.client.get(reverse('dashboard_redirect'), follow=True)
        self.assertRedirects(res, reverse('warden_dashboard'))
        self.client.logout()

        # 3. Admin
        self.client.login(username='admin_user', password=self.password)
        res = self.client.get(reverse('dashboard_redirect'), follow=True)
        self.assertRedirects(res, reverse('admin_dashboard'))
        self.client.logout()
