from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from applications.models import Student
from hostels.models import Hostel, Room
from allocations.models import Allocation
from .models import MaintenanceStaff, MaintenanceRequest

User = get_user_model()


class MaintenanceAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Secur3Pass123!"

        # Admin
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@college.edu",
            password=self.password,
            role=User.ROLE_ADMIN
        )

        # Warden
        self.warden = User.objects.create_user(
            username="warden_user",
            email="warden@college.edu",
            password=self.password,
            role=User.ROLE_WARDEN
        )

        # Hostel & Room
        self.hostel = Hostel.objects.create(
            name="Block A",
            hostel_type=Hostel.TYPE_BOYS,
            total_rooms=10,
            warden=self.warden
        )
        self.room = Room.objects.create(
            hostel=self.hostel,
            floor_no=1,
            room_no="101",
            capacity=2,
            room_type=Room.TYPE_DOUBLE
        )

        # Student & Active Allocation
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="STU-001",
            name="Student Alpha",
            gender=Student.GENDER_MALE,
            course="B.Tech IT",
            year=1,
            phone="9876543210",
            email="student@college.edu",
            guardian_name="Guardian Alpha",
            guardian_phone="9876543211",
            merit_score=80.0
        )
        self.allocation = Allocation.objects.create(
            student=self.student,
            room=self.room,
            is_active=True,
            status=Allocation.STATUS_CONFIRMED,
            due_date=timezone.now().date() + timezone.timedelta(days=7)
        )

        # Maintenance Staff
        self.staff = MaintenanceStaff.objects.create(
            name="Ramesh Electrician",
            phone="9988776655",
            specialization="Electrician",
            active=True
        )

    def test_maintenance_list_view_authenticated(self):
        self.client.login(username="student_user", password=self.password)
        res = self.client.get(reverse('maintenance_list'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'maintenance/maintenance_list.html')

    def test_student_create_maintenance_ticket(self):
        self.client.login(username="student_user", password=self.password)
        post_data = {
            'category': MaintenanceRequest.CAT_ELECTRICITY,
            'priority': MaintenanceRequest.PRIO_HIGH,
            'description': 'Main light bulb is flickering constantly.',
        }
        res = self.client.post(reverse('maintenance_create'), post_data)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(MaintenanceRequest.objects.count(), 1)
        ticket = MaintenanceRequest.objects.first()
        self.assertEqual(ticket.category, MaintenanceRequest.CAT_ELECTRICITY)
        self.assertEqual(ticket.status, MaintenanceRequest.STATUS_OPEN)
        self.assertEqual(ticket.room, self.room)

    def test_warden_update_ticket_status_and_assign_staff(self):
        ticket = MaintenanceRequest.objects.create(
            student=self.student,
            room=self.room,
            category=MaintenanceRequest.CAT_WATER,
            priority=MaintenanceRequest.PRIO_MEDIUM,
            description="Leaky tap in bathroom",
            status=MaintenanceRequest.STATUS_OPEN
        )

        self.client.login(username="warden_user", password=self.password)
        res = self.client.post(reverse('maintenance_update_status', args=[ticket.pk]), {
            'status': MaintenanceRequest.STATUS_RESOLVED,
            'assigned_staff': self.staff.pk,
            'warden_notes': 'Repaired by Ramesh.',
            'resolution_notes': 'Replaced washbasin washer.'
        })
        self.assertEqual(res.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, MaintenanceRequest.STATUS_RESOLVED)
        self.assertEqual(ticket.assigned_staff, self.staff)
        self.assertIsNotNone(ticket.resolved_at)

    def test_student_rate_resolved_ticket(self):
        ticket = MaintenanceRequest.objects.create(
            student=self.student,
            room=self.room,
            category=MaintenanceRequest.CAT_WATER,
            priority=MaintenanceRequest.PRIO_MEDIUM,
            description="Leaky tap in bathroom",
            status=MaintenanceRequest.STATUS_RESOLVED
        )

        self.client.login(username="student_user", password=self.password)
        res = self.client.post(reverse('maintenance_rate', args=[ticket.pk]), {
            'rating': 5,
            'feedback': 'Great fast service, completely fixed!',
        })
        self.assertEqual(res.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.rating, 5)
        self.assertEqual(ticket.status, MaintenanceRequest.STATUS_CLOSED)
