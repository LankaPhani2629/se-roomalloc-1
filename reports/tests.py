from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from hostels.models import Hostel, Room

User = get_user_model()


class ReportsExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"

        self.admin_user = User.objects.create_user(
            username="rep_admin",
            email="admin@college.edu",
            password=self.password,
            role=User.ROLE_ADMIN
        )

        self.hostel = Hostel.objects.create(
            name="Saraswati Girls Hostel",
            hostel_type=Hostel.TYPE_GIRLS,
            total_rooms=5
        )
        self.room = Room.objects.create(
            hostel=self.hostel,
            floor_no=1,
            room_no="S-101",
            capacity=3,
            room_type=Room.TYPE_TRIPLE,
            occupied_count=1,
            status=Room.STATUS_AVAILABLE
        )

    def test_occupancy_report_html_view(self):
        """Test occupancy report HTML table view."""
        self.client.login(username="rep_admin", password=self.password)
        response = self.client.get(reverse('occupancy_report'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saraswati Girls Hostel")
        self.assertContains(response, "S-101")

    def test_occupancy_report_pdf_export(self):
        """Test occupancy report export to PDF (content-type application/pdf)."""
        self.client.login(username="rep_admin", password=self.password)
        response = self.client.get(reverse('occupancy_report') + "?export=pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="Hostel_Occupancy_Report.pdf"', response['Content-Disposition'])

    def test_occupancy_report_excel_export(self):
        """Test occupancy report export to Excel (openpyxl xlsx)."""
        self.client.login(username="rep_admin", password=self.password)
        response = self.client.get(reverse('occupancy_report') + "?export=excel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment; filename="Hostel_Occupancy_Report.xlsx"', response['Content-Disposition'])
