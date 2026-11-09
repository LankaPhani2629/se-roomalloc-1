from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from applications.models import Student, Application
from hostels.models import Hostel, Room
from allocations.models import Allocation, RoomChangeRequest
from allocations.services import (
    allocate_room_to_student,
    process_room_change_or_vacate,
    run_automatic_allocation
)

User = get_user_model()


class AllocationRulesAndWorkflowsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"

        # Create Warden
        self.warden = User.objects.create_user(
            username="warden_alloc",
            email="warden_alloc@college.edu",
            password=self.password,
            role=User.ROLE_WARDEN
        )

        # Hostels
        self.boys_hostel = Hostel.objects.create(
            name="Ganga Boys Hostel",
            hostel_type=Hostel.TYPE_BOYS,
            total_rooms=5,
            warden=self.warden
        )
        self.girls_hostel = Hostel.objects.create(
            name="Yamuna Girls Hostel",
            hostel_type=Hostel.TYPE_GIRLS,
            total_rooms=5,
            warden=self.warden
        )

        # Rooms
        self.boys_room_1 = Room.objects.create(
            hostel=self.boys_hostel,
            floor_no=1,
            room_no="B-101",
            capacity=2,
            room_type=Room.TYPE_DOUBLE,
            occupied_count=0,
            status=Room.STATUS_AVAILABLE
        )
        self.boys_room_2 = Room.objects.create(
            hostel=self.boys_hostel,
            floor_no=1,
            room_no="B-102",
            capacity=2,
            room_type=Room.TYPE_DOUBLE,
            occupied_count=0,
            status=Room.STATUS_AVAILABLE
        )
        self.girls_room_1 = Room.objects.create(
            hostel=self.girls_hostel,
            floor_no=1,
            room_no="G-101",
            capacity=2,
            room_type=Room.TYPE_DOUBLE,
            occupied_count=0,
            status=Room.STATUS_AVAILABLE
        )

        # Male Student
        self.male_user = User.objects.create_user(
            username="bob_male",
            email="bob@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.male_student = Student.objects.create(
            user=self.male_user,
            student_id="ROLL-BOY-01",
            name="Bob Smith",
            gender=Student.GENDER_MALE,
            course="B.Tech ME",
            year=1,
            phone="9876543201",
            email="bob@college.edu",
            address="Street 1",
            guardian_name="Guardian Bob",
            guardian_phone="9876543202",
            merit_score=88.0
        )

        # Female Student
        self.female_user = User.objects.create_user(
            username="clara_female",
            email="clara@college.edu",
            password=self.password,
            role=User.ROLE_STUDENT
        )
        self.female_student = Student.objects.create(
            user=self.female_user,
            student_id="ROLL-GIRL-01",
            name="Clara Oswald",
            gender=Student.GENDER_FEMALE,
            course="B.Tech EE",
            year=1,
            phone="9876543203",
            email="clara@college.edu",
            address="Street 2",
            guardian_name="Guardian Clara",
            guardian_phone="9876543204",
            merit_score=91.0
        )

    def test_allocation_with_free_capacity(self):
        """Test allocating a room with free capacity increments occupied_count and creates Allocation."""
        alloc = allocate_room_to_student(
            student=self.male_student,
            room=self.boys_room_1,
            due_days=7
        )
        self.assertIsNotNone(alloc.pk)
        self.assertEqual(alloc.status, Allocation.STATUS_PENDING_PAYMENT)
        self.assertTrue(alloc.is_active)

        self.boys_room_1.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 1)
        self.assertEqual(self.boys_room_1.vacancy, 1)

    def test_full_room_denied(self):
        """Test room cannot exceed capacity: allocating to a full room raises ValidationError."""
        # Fill boys_room_1 to capacity (2)
        student_extra1 = Student.objects.create(
            user=User.objects.create_user(username="u_extra1", email="e1@col.edu", password=self.password, role=User.ROLE_STUDENT),
            student_id="ROLL-EX-01", name="Ex One", gender=Student.GENDER_MALE, course="CS", year=1,
            phone="111", email="e1@col.edu", address="A", guardian_name="G", guardian_phone="111"
        )
        student_extra2 = Student.objects.create(
            user=User.objects.create_user(username="u_extra2", email="e2@col.edu", password=self.password, role=User.ROLE_STUDENT),
            student_id="ROLL-EX-02", name="Ex Two", gender=Student.GENDER_MALE, course="CS", year=1,
            phone="222", email="e2@col.edu", address="B", guardian_name="G", guardian_phone="222"
        )

        allocate_room_to_student(student=student_extra1, room=self.boys_room_1)
        allocate_room_to_student(student=student_extra2, room=self.boys_room_1)

        self.boys_room_1.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 2)
        self.assertEqual(self.boys_room_1.status, Room.STATUS_FULL)

        # Attempt to allocate 3rd student to full room
        with self.assertRaises(ValidationError) as ctx:
            allocate_room_to_student(student=self.male_student, room=self.boys_room_1)
        self.assertIn("capacity", str(ctx.exception).lower())

    def test_wrong_gender_hostel_denied(self):
        """Test boys and girls can only be allotted to their respective hostels."""
        # Boy to Girls Hostel should be denied
        with self.assertRaises(ValidationError) as ctx:
            allocate_room_to_student(student=self.male_student, room=self.girls_room_1)
        self.assertIn("male students can only be allotted to boys hostels", str(ctx.exception).lower())

        # Girl to Boys Hostel should be denied
        with self.assertRaises(ValidationError) as ctx2:
            allocate_room_to_student(student=self.female_student, room=self.boys_room_1)
        self.assertIn("female students can only be allotted to girls hostels", str(ctx2.exception).lower())

    def test_one_active_allotment_per_student(self):
        """Test a student can have only one active allotment."""
        # First allocation
        allocate_room_to_student(student=self.male_student, room=self.boys_room_1)

        # Attempting second allocation to boys_room_2 must fail
        with self.assertRaises(ValidationError) as ctx:
            allocate_room_to_student(student=self.male_student, room=self.boys_room_2)
        self.assertIn("already has an active room allotment", str(ctx.exception).lower())

    def test_room_change_workflow(self):
        """Test student requests room change; warden approves; both rooms' occupied_count update atomically."""
        # Initial allocation in boys_room_1
        alloc = allocate_room_to_student(student=self.male_student, room=self.boys_room_1)
        self.boys_room_1.refresh_from_db()
        self.boys_room_2.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 1)
        self.assertEqual(self.boys_room_2.occupied_count, 0)

        # Create change request
        change_req = RoomChangeRequest.objects.create(
            student=self.male_student,
            current_allocation=alloc,
            request_type=RoomChangeRequest.TYPE_CHANGE,
            preferred_room_type="DOUBLE",
            target_room=self.boys_room_2,
            reason="Want to move to Room B-102."
        )

        # Warden approves
        process_room_change_or_vacate(
            change_request=change_req,
            warden_user=self.warden,
            decision='APPROVED',
            remarks='Approved room transfer.',
            target_room=self.boys_room_2
        )

        # Verify old room was decremented and new room incremented
        self.boys_room_1.refresh_from_db()
        self.boys_room_2.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 0)
        self.assertEqual(self.boys_room_2.occupied_count, 1)

        # Old allocation is vacated
        alloc.refresh_from_db()
        self.assertFalse(alloc.is_active)
        self.assertEqual(alloc.status, Allocation.STATUS_VACATED)

        # New active allocation created in boys_room_2
        new_alloc = Allocation.objects.get(student=self.male_student, is_active=True)
        self.assertEqual(new_alloc.room, self.boys_room_2)

    def test_vacating_workflow(self):
        """Test student requests vacating; warden approves; room count decremented and date recorded."""
        alloc = allocate_room_to_student(student=self.male_student, room=self.boys_room_1)
        self.boys_room_1.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 1)

        vacate_req = RoomChangeRequest.objects.create(
            student=self.male_student,
            current_allocation=alloc,
            request_type=RoomChangeRequest.TYPE_VACATE,
            reason="Graduating early."
        )

        process_room_change_or_vacate(
            change_request=vacate_req,
            warden_user=self.warden,
            decision='APPROVED',
            remarks='Vacated room successfully.'
        )

        self.boys_room_1.refresh_from_db()
        self.assertEqual(self.boys_room_1.occupied_count, 0)

        alloc.refresh_from_db()
        self.assertFalse(alloc.is_active)
        self.assertEqual(alloc.status, Allocation.STATUS_VACATED)
        self.assertEqual(alloc.vacate_date, timezone.now().date())
