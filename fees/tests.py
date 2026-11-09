from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from applications.models import Student
from hostels.models import Hostel, Room
from allocations.models import Allocation
from allocations.services import allocate_room_to_student
from fees.models import FeePayment, FeeStructure

User = get_user_model()


class FeePaymentAndConfirmationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"

        # Accountant user
        self.accountant = User.objects.create_user(
            username="accountant_user",
            email="accountant@college.edu",
            password=self.password,
            role=User.ROLE_ACCOUNTANT
        )

        # Student user and profile
        self.student_user = User.objects.create_user(
            username="fee_student",
            email="feestudent@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="ROLL-FEE-01",
            name="Fee Test Student",
            gender=Student.GENDER_MALE,
            course="B.Com",
            year=1,
            phone="9876500001",
            email="feestudent@college.edu",
            address="Addr",
            guardian_name="G",
            guardian_phone="9876500002",
            merit_score=80.0
        )

        # Hostel & Room
        self.hostel = Hostel.objects.create(
            name="Tagore Boys Hostel",
            hostel_type=Hostel.TYPE_BOYS,
            total_rooms=10
        )
        self.room = Room.objects.create(
            hostel=self.hostel,
            floor_no=1,
            room_no="T-101",
            capacity=2,
            room_type=Room.TYPE_DOUBLE,
            occupied_count=0,
            status=Room.STATUS_AVAILABLE
        )

        # Fee Structure
        self.fee_structure = FeeStructure.objects.create(
            room_type=Room.TYPE_DOUBLE,
            academic_year="2026-2027",
            amount=25000.00,
            due_days=7
        )

    def test_fee_payment_on_time_confirms_allotment(self):
        """Test fee payment on or before due date confirms allotment and generates printable receipt."""
        alloc = allocate_room_to_student(student=self.student, room=self.room, due_days=7)
        self.assertEqual(alloc.status, Allocation.STATUS_PENDING_PAYMENT)

        self.client.login(username="accountant_user", password=self.password)
        response = self.client.post(reverse('record_payment'), {
            'allocation': alloc.pk,
            'amount': 25000.00,
            'payment_mode': 'ONLINE',
            'transaction_id': 'TXN-ONLINE-999',
            'remarks': 'Annual fee paid in full.'
        })

        # Payment creates FeePayment and redirects to printable receipt
        self.assertEqual(response.status_code, 302)
        payment = FeePayment.objects.filter(allocation=alloc).first()
        self.assertIsNotNone(payment)
        self.assertTrue(payment.receipt_no.startswith("RCP"))

        # Allocation is now CONFIRMED
        alloc.refresh_from_db()
        self.assertEqual(alloc.status, Allocation.STATUS_CONFIRMED)
        self.assertIsNotNone(alloc.check_in_date)

    def test_fee_payment_after_due_date_expires_allotment(self):
        """Test business rule: allotment is confirmed ONLY after fee is paid by due date; otherwise Expired."""
        alloc = allocate_room_to_student(student=self.student, room=self.room, due_days=7)
        self.room.refresh_from_db()
        self.assertEqual(self.room.occupied_count, 1)

        # Simulate due date expired in the past
        alloc.due_date = timezone.now().date() - timedelta(days=2)
        alloc.save()

        self.client.login(username="accountant_user", password=self.password)
        response = self.client.post(reverse('record_payment'), {
            'allocation': alloc.pk,
            'amount': 25000.00,
            'payment_mode': 'ONLINE',
            'transaction_id': 'TXN-EXPIRED-001',
            'remarks': 'Attempt late payment.'
        })

        alloc.refresh_from_db()
        self.room.refresh_from_db()

        # Allocation marked as EXPIRED and inactive
        self.assertEqual(alloc.status, Allocation.STATUS_EXPIRED)
        self.assertFalse(alloc.is_active)

        # Room occupied count is decremented / released back to inventory
        self.assertEqual(self.room.occupied_count, 0)
