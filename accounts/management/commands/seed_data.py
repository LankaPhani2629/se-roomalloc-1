from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from applications.models import Student, ApplicationPeriod
from hostels.models import Hostel, Room
from fees.models import FeeStructure
from allocations.models import AllocationRule


class Command(BaseCommand):
    help = "Seeds database with demo accounts (Admin, Warden, Student, Accountant), Hostels, Rooms, and Rules."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with demo data..."))

        # 1. Administrator
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                'email': 'admin@college.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()

        # 2. Warden
        warden_user, _ = User.objects.get_or_create(
            username="warden",
            defaults={
                'email': 'warden@college.edu',
                'first_name': 'Vikram',
                'last_name': 'Rathore',
                'role': User.ROLE_WARDEN,
                'is_staff': True,
            }
        )
        warden_user.set_password("warden123")
        warden_user.save()

        # 3. Accountant
        accountant_user, _ = User.objects.get_or_create(
            username="accountant",
            defaults={
                'email': 'accounts@college.edu',
                'first_name': 'Ramesh',
                'last_name': 'Gupta',
                'role': User.ROLE_ACCOUNTANT,
                'is_staff': True,
            }
        )
        accountant_user.set_password("accountant123")
        accountant_user.save()

        # 4. Student (Boy)
        boy_user, _ = User.objects.get_or_create(
            username="student_boy",
            defaults={
                'email': 'rahul@college.edu',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'role': User.ROLE_STUDENT,
                'phone': '9876543210'
            }
        )
        boy_user.set_password("student123")
        boy_user.save()

        Student.objects.update_or_create(
            user=boy_user,
            defaults={
                'student_id': '2026CS101',
                'name': 'Rahul Sharma',
                'gender': Student.GENDER_MALE,
                'course': 'B.Tech Computer Science',
                'year': 1,
                'phone': '9876543210',
                'email': 'rahul@college.edu',
                'address': 'Flat 102, Green Park, New Delhi',
                'guardian_name': 'Suresh Sharma',
                'guardian_phone': '9876543219',
                'merit_score': 88.5
            }
        )

        # 5. Student (Girl)
        girl_user, _ = User.objects.get_or_create(
            username="student_girl",
            defaults={
                'email': 'pooja@college.edu',
                'first_name': 'Pooja',
                'last_name': 'Verma',
                'role': User.ROLE_STUDENT,
                'phone': '9123456780'
            }
        )
        girl_user.set_password("student123")
        girl_user.save()

        Student.objects.update_or_create(
            user=girl_user,
            defaults={
                'student_id': '2026EC202',
                'name': 'Pooja Verma',
                'gender': Student.GENDER_FEMALE,
                'course': 'B.Tech Electronics & Comm.',
                'year': 2,
                'phone': '9123456780',
                'email': 'pooja@college.edu',
                'address': 'Plot 45, Model Town, Jaipur',
                'guardian_name': 'Anil Verma',
                'guardian_phone': '9123456789',
                'merit_score': 93.0
            }
        )

        # 6. Hostels
        boys_hostel, _ = Hostel.objects.get_or_create(
            name="Ganga Boys Hostel",
            defaults={
                'hostel_type': Hostel.TYPE_BOYS,
                'warden': warden_user,
                'description': 'Senior Boys Hostel Block with Wi-Fi, Gym, and Common Study Area.'
            }
        )
        girls_hostel, _ = Hostel.objects.get_or_create(
            name="Kaveri Girls Hostel",
            defaults={
                'hostel_type': Hostel.TYPE_GIRLS,
                'warden': warden_user,
                'description': 'Girls Residential Block with 24/7 Security, Library, and Dining Hall.'
            }
        )

        # 7. Rooms
        boys_rooms = [
            (0, 'G-01', Room.TYPE_SINGLE, 1),
            (0, 'G-02', Room.TYPE_DOUBLE, 2),
            (1, 'G-101', Room.TYPE_DOUBLE, 2),
            (1, 'G-102', Room.TYPE_TRIPLE, 3),
            (2, 'G-201', Room.TYPE_FOUR, 4),
        ]
        for fl, r_no, r_type, cap in boys_rooms:
            Room.objects.get_or_create(
                hostel=boys_hostel,
                room_no=r_no,
                defaults={
                    'floor_no': fl,
                    'room_type': r_type,
                    'capacity': cap,
                    'status': Room.STATUS_AVAILABLE,
                    'occupied_count': 0
                }
            )
        boys_hostel.update_room_count()

        girls_rooms = [
            (0, 'K-01', Room.TYPE_SINGLE, 1),
            (0, 'K-02', Room.TYPE_DOUBLE, 2),
            (1, 'K-101', Room.TYPE_DOUBLE, 2),
            (1, 'K-102', Room.TYPE_TRIPLE, 3),
            (2, 'K-201', Room.TYPE_FOUR, 4),
        ]
        for fl, r_no, r_type, cap in girls_rooms:
            Room.objects.get_or_create(
                hostel=girls_hostel,
                room_no=r_no,
                defaults={
                    'floor_no': fl,
                    'room_type': r_type,
                    'capacity': cap,
                    'status': Room.STATUS_AVAILABLE,
                    'occupied_count': 0
                }
            )
        girls_hostel.update_room_count()

        # 8. Active Application Window
        today = timezone.now().date()
        ApplicationPeriod.objects.get_or_create(
            academic_year='2026-2027',
            defaults={
                'start_date': today - timedelta(days=2),
                'end_date': today + timedelta(days=30),
                'is_active': True,
                'description': 'Fall 2026 Hostel Admissions'
            }
        )

        # 9. Fee Structures
        fees = [
            (Room.TYPE_SINGLE, '2026-2027', 35000.00, 7),
            (Room.TYPE_DOUBLE, '2026-2027', 25000.00, 7),
            (Room.TYPE_TRIPLE, '2026-2027', 20000.00, 7),
            (Room.TYPE_FOUR, '2026-2027', 15000.00, 7),
        ]
        for r_type, acad_yr, amt, due_days in fees:
            FeeStructure.objects.get_or_create(
                room_type=r_type,
                academic_year=acad_yr,
                defaults={
                    'amount': amt,
                    'due_days': due_days,
                    'description': f"Standard fee for {r_type} room"
                }
            )

        # 10. Allocation Priority Rules
        AllocationRule.objects.get_or_create(
            name="1st Year Student Priority",
            defaults={
                'gender': AllocationRule.GENDER_ALL,
                'year_of_study': 1,
                'priority_order': 1,
                'merit_weight': 10,
                'is_active': True,
                'description': 'Priority weighting for fresh first-year entrants.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Database successfully seeded!"))
        self.stdout.write(self.style.SUCCESS(
            "\nDemo Accounts created:\n"
            "  - Admin:      admin / admin123\n"
            "  - Warden:     warden / warden123\n"
            "  - Student 1:  student_boy / student123 (Rahul Sharma, Male)\n"
            "  - Student 2:  student_girl / student123 (Pooja Verma, Female)\n"
            "  - Accountant: accountant / accountant123\n"
        ))

