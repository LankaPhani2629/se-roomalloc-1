from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from applications.models import Student
from hostels.models import Hostel, Room
from allocations.models import Allocation
from .models import MessMenu, MessAttendance, MessFeedback, MessFee

User = get_user_model()


class MessAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "PassMess123!"

        # Admin
        self.admin = User.objects.create_user(
            username="admin_mess",
            email="admin_mess@college.edu",
            password=self.password,
            role=User.ROLE_ADMIN
        )

        # Warden
        self.warden = User.objects.create_user(
            username="warden_mess",
            email="warden_mess@college.edu",
            password=self.password,
            role=User.ROLE_WARDEN
        )

        # Accountant
        self.accountant = User.objects.create_user(
            username="accountant_mess",
            email="accountant_mess@college.edu",
            password=self.password,
            role=User.ROLE_ACCOUNTANT
        )

        # Student & Hostel
        self.hostel = Hostel.objects.create(
            name="Dining Hostel 1",
            hostel_type=Hostel.TYPE_BOYS,
            total_rooms=5,
            warden=self.warden
        )
        self.room = Room.objects.create(
            hostel=self.hostel,
            floor_no=1,
            room_no="201",
            capacity=2,
            room_type=Room.TYPE_DOUBLE
        )

        self.student_user = User.objects.create_user(
            username="student_mess",
            email="student_mess@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="MESS-STU-01",
            name="Mess Student",
            gender=Student.GENDER_MALE,
            course="B.Tech ECE",
            year=2,
            phone="9876543299",
            email="student_mess@college.edu",
            guardian_name="Guardian Mess",
            guardian_phone="9876543298",
            merit_score=82.5
        )
        self.allocation = Allocation.objects.create(
            student=self.student,
            room=self.room,
            is_active=True,
            status=Allocation.STATUS_CONFIRMED,
            due_date=timezone.now().date() + timedelta(days=7)
        )

    def test_warden_publish_menu(self):
        self.client.login(username="warden_mess", password=self.password)
        today = timezone.now().date()
        res = self.client.post(reverse('mess_menu_publish'), {
            'hostel': self.hostel.pk,
            'date': today.strftime('%Y-%m-%d'),
            'meal': MessMenu.MEAL_BREAKFAST,
            'items': 'Idli, Vada, Sambhar, Chutney, Tea'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(MessMenu.objects.count(), 1)
        menu = MessMenu.objects.first()
        self.assertEqual(menu.meal, MessMenu.MEAL_BREAKFAST)
        self.assertIn('Idli', menu.items)

    def test_student_menu_view_and_skip_meal(self):
        today = timezone.now().date()
        menu = MessMenu.objects.create(
            hostel=self.hostel,
            date=today,
            meal=MessMenu.MEAL_LUNCH,
            items='Rice, Dal, Paneer Butter Masala, Curd'
        )

        self.client.login(username="student_mess", password=self.password)
        # View menu
        res = self.client.get(reverse('mess_menu'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Paneer Butter Masala')

        # Skip meal
        skip_res = self.client.post(reverse('mess_skip_meal'), {
            'date': today.strftime('%Y-%m-%d'),
            'meal': MessMenu.MEAL_LUNCH,
            'action': 'skip'
        })
        self.assertEqual(skip_res.status_code, 302)
        self.assertEqual(MessAttendance.objects.count(), 1)
        att = MessAttendance.objects.first()
        self.assertTrue(att.is_skipped)

    def test_student_meal_feedback(self):
        self.client.login(username="student_mess", password=self.password)
        res = self.client.post(reverse('mess_feedback'), {
            'meal': MessMenu.MEAL_DINNER,
            'rating': 5,
            'comments': 'Dinner was hot and fresh!'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(MessFeedback.objects.count(), 1)
        fb = MessFeedback.objects.first()
        self.assertEqual(fb.rating, 5)

    def test_accountant_generate_billing(self):
        # Create a skipped meal for this student
        now = timezone.now()
        MessAttendance.objects.create(
            student=self.student,
            date=now.date(),
            meal=MessMenu.MEAL_LUNCH,
            is_skipped=True
        )

        self.client.login(username="accountant_mess", password=self.password)
        res = self.client.post(reverse('mess_billing'), {
            'month': now.month,
            'year': now.year,
            'base_amount': '4500.00',
            'rebate_per_meal': '40.00'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(MessFee.objects.count(), 1)
        bill = MessFee.objects.first()
        self.assertEqual(bill.skipped_meals_count, 1)
        self.assertEqual(bill.rebate_amount, 40.0)
        self.assertEqual(bill.total_amount, 4460.0)
