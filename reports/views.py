from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

from accounts.decorators import admin_required, warden_required, student_required, accountant_required, role_required
from hostels.models import Hostel, Room
from applications.models import Student, Application
from allocations.models import Allocation, RoomChangeRequest
from fees.models import FeePayment, FeeStructure
from complaints.models import Complaint
from .exports import generate_pdf_table_report, generate_excel_table_report


# ==========================================
# 1. ROLE-SPECIFIC DASHBOARDS
# ==========================================

@login_required
@admin_required
def admin_dashboard_view(request):
    """Admin dashboard: total, occupied and vacant rooms, pending applications, dues."""
    total_hostels = Hostel.objects.count()
    total_rooms = Room.objects.count()

    total_capacity = sum(r.capacity for r in Room.objects.all())
    total_occupied = sum(r.occupied_count for r in Room.objects.all())
    total_vacant = max(0, total_capacity - total_occupied)

    pending_applications_count = Application.objects.filter(status=Application.STATUS_PENDING).count()
    pending_dues_count = Allocation.objects.filter(status=Allocation.STATUS_PENDING_PAYMENT, is_active=True).count()

    # Total collected fees
    total_revenue = FeePayment.objects.filter(status=FeePayment.STATUS_SUCCESS).aggregate(total=Sum('amount'))['total'] or 0

    recent_applications = Application.objects.select_related('student').order_by('-application_date')[:5]
    hostels_summary = Hostel.objects.all().prefetch_related('rooms')

    return render(request, 'reports/admin_dashboard.html', {
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
        'total_occupied': total_occupied,
        'total_vacant': total_vacant,
        'pending_applications_count': pending_applications_count,
        'pending_dues_count': pending_dues_count,
        'total_revenue': total_revenue,
        'recent_applications': recent_applications,
        'hostels_summary': hostels_summary,
    })


@login_required
@warden_required
def warden_dashboard_view(request):
    """Warden dashboard: pending applications, room requests, complaints, hostel summary."""
    pending_apps = Application.objects.filter(status=Application.STATUS_PENDING).count()
    pending_room_requests = RoomChangeRequest.objects.filter(status=RoomChangeRequest.STATUS_PENDING).count()
    open_complaints = Complaint.objects.filter(status__in=[Complaint.STATUS_OPEN, Complaint.STATUS_IN_PROGRESS]).count()

    assigned_hostels = Hostel.objects.filter(warden=request.user) if not request.user.is_superuser else Hostel.objects.all()

    recent_pending_apps = Application.objects.select_related('student').filter(
        status=Application.STATUS_PENDING
    ).order_by('-application_date')[:5]

    recent_room_requests = RoomChangeRequest.objects.select_related('student', 'current_allocation__room').filter(
        status=RoomChangeRequest.STATUS_PENDING
    ).order_by('-created_at')[:5]

    return render(request, 'reports/warden_dashboard.html', {
        'pending_apps': pending_apps,
        'pending_room_requests': pending_room_requests,
        'open_complaints': open_complaints,
        'assigned_hostels': assigned_hostels,
        'recent_pending_apps': recent_pending_apps,
        'recent_room_requests': recent_room_requests,
    })


@login_required
@student_required
def student_dashboard_view(request):
    """Student dashboard: status, room details, fee dues, active complaints."""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return redirect('home')

    active_allocation = Allocation.objects.select_related('room', 'room__hostel').filter(
        student=student,
        is_active=True
    ).first()

    recent_app = student.applications.order_by('-application_date').first()
    active_complaints = student.complaints.filter(status__in=[Complaint.STATUS_OPEN, Complaint.STATUS_IN_PROGRESS])
    recent_payments = FeePayment.objects.filter(allocation__student=student).order_by('-payment_date')[:3]

    expected_fee = None
    if active_allocation:
        fs = FeeStructure.objects.filter(
            room_type=active_allocation.room.room_type,
            academic_year=active_allocation.academic_year
        ).first()
        if fs:
            expected_fee = fs.amount

    return render(request, 'reports/student_dashboard.html', {
        'student': student,
        'active_allocation': active_allocation,
        'recent_app': recent_app,
        'active_complaints': active_complaints,
        'recent_payments': recent_payments,
        'expected_fee': expected_fee,
        'today': timezone.now().date(),
    })


@login_required
@accountant_required
def accountant_dashboard_view(request):
    """Accountant dashboard: collections, pending dues, recent payments."""
    total_collections = FeePayment.objects.filter(
        status=FeePayment.STATUS_SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or 0

    pending_dues_count = Allocation.objects.filter(
        status=Allocation.STATUS_PENDING_PAYMENT,
        is_active=True
    ).count()

    recent_payments = FeePayment.objects.select_related('allocation__student', 'recorded_by').order_by('-payment_date')[:8]
    fee_structures = FeeStructure.objects.all()

    return render(request, 'reports/accountant_dashboard.html', {
        'total_collections': total_collections,
        'pending_dues_count': pending_dues_count,
        'recent_payments': recent_payments,
        'fee_structures': fee_structures,
    })


# ==========================================
# 2. REPORTS HUB & EXPORT HANDLERS
# ==========================================

@login_required
@role_required('ADMIN', 'ACCOUNTANT')
def reports_hub_view(request):
    """Reports navigation overview."""
    return render(request, 'reports/hub.html')


@login_required
@role_required('ADMIN', 'WARDEN', 'ACCOUNTANT')
def occupancy_report_view(request):
    """Occupancy Report: Hostel-wise and floor-wise."""
    export_format = request.GET.get('export')
    rooms = Room.objects.select_related('hostel').order_by('hostel__name', 'floor_no', 'room_no')

    if export_format in ['pdf', 'excel']:
        headers = ['Hostel Name', 'Gender Type', 'Floor', 'Room No', 'Type', 'Capacity', 'Occupied', 'Vacancy', 'Occupancy %']
        rows = []
        for r in rooms:
            occ_pct = f"{int((r.occupied_count / r.capacity) * 100)}%" if r.capacity else "0%"
            rows.append([
                r.hostel.name,
                r.hostel.get_hostel_type_display(),
                f"Floor {r.floor_no}",
                f"Rm {r.room_no}",
                r.get_room_type_display(),
                r.capacity,
                r.occupied_count,
                r.vacancy,
                occ_pct
            ])

        if export_format == 'pdf':
            return generate_pdf_table_report("Occupancy Report", headers, rows, filename="Hostel_Occupancy_Report.pdf")
        else:
            return generate_excel_table_report("Occupancy Report", headers, rows, filename="Hostel_Occupancy_Report.xlsx")

    return render(request, 'reports/occupancy_report.html', {'rooms': rooms})


@login_required
@role_required('ADMIN', 'WARDEN', 'ACCOUNTANT')
def vacancy_report_view(request):
    """Vacancy Report: Rooms with free capacity."""
    export_format = request.GET.get('export')
    vacant_rooms = Room.objects.select_related('hostel').filter(
        status=Room.STATUS_AVAILABLE,
        occupied_count__lt=F('capacity')
    ).order_by('hostel__name', 'floor_no', 'room_no')

    if export_format in ['pdf', 'excel']:
        headers = ['Hostel Name', 'Hostel Type', 'Floor', 'Room No', 'Room Type', 'Total Beds', 'Vacant Beds']
        rows = []
        for r in vacant_rooms:
            rows.append([
                r.hostel.name,
                r.hostel.get_hostel_type_display(),
                f"Floor {r.floor_no}",
                f"Rm {r.room_no}",
                r.get_room_type_display(),
                r.capacity,
                r.vacancy
            ])

        if export_format == 'pdf':
            return generate_pdf_table_report("Room Vacancy Report", headers, rows, filename="Hostel_Vacancy_Report.pdf")
        else:
            return generate_excel_table_report("Room Vacancy Report", headers, rows, filename="Hostel_Vacancy_Report.xlsx")

    return render(request, 'reports/vacancy_report.html', {'vacant_rooms': vacant_rooms})


@login_required
@role_required('ADMIN', 'WARDEN', 'ACCOUNTANT')
def allocation_list_report_view(request):
    """Allocation List Report: all student room allotments."""
    export_format = request.GET.get('export')
    allocations = Allocation.objects.select_related('student', 'room', 'room__hostel').order_by('-allocation_date')

    if export_format in ['pdf', 'excel']:
        headers = ['Alloc ID', 'Student Name', 'Roll ID', 'Gender', 'Hostel', 'Room No', 'Allotted Date', 'Due Date', 'Status']
        rows = []
        for a in allocations:
            rows.append([
                f"#AL-{a.pk}",
                a.student.name,
                a.student.student_id,
                a.student.get_gender_display(),
                a.room.hostel.name,
                a.room.room_no,
                str(a.allocation_date),
                str(a.due_date),
                a.get_status_display()
            ])

        if export_format == 'pdf':
            return generate_pdf_table_report("Allocation List Report", headers, rows, filename="Room_Allotments_Report.pdf")
        else:
            return generate_excel_table_report("Allocation List Report", headers, rows, filename="Room_Allotments_Report.xlsx")

    return render(request, 'reports/allocation_report.html', {'allocations': allocations})


@login_required
@role_required('ADMIN', 'ACCOUNTANT')
def fee_dues_report_view(request):
    """Fee Dues Report: pending and overdue payments."""
    export_format = request.GET.get('export')
    today = timezone.now().date()
    pending_allocations = Allocation.objects.select_related(
        'student', 'room', 'room__hostel'
    ).filter(
        status=Allocation.STATUS_PENDING_PAYMENT,
        is_active=True
    ).order_by('due_date')

    if export_format in ['pdf', 'excel']:
        headers = ['Allotment', 'Student Name', 'Roll ID', 'Hostel', 'Room No', 'Allotted On', 'Due Date', 'Overdue?']
        rows = []
        for a in pending_allocations:
            is_overdue = "YES (EXPIRED)" if a.due_date < today else "NO"
            rows.append([
                f"#AL-{a.pk}",
                a.student.name,
                a.student.student_id,
                a.room.hostel.name,
                a.room.room_no,
                str(a.allocation_date),
                str(a.due_date),
                is_overdue
            ])

        if export_format == 'pdf':
            return generate_pdf_table_report("Fee Dues Report", headers, rows, filename="Fee_Dues_Report.pdf")
        else:
            return generate_excel_table_report("Fee Dues Report", headers, rows, filename="Fee_Dues_Report.xlsx")

    return render(request, 'reports/fee_dues_report.html', {
        'pending_allocations': pending_allocations,
        'today': today
    })


@login_required
@role_required('ADMIN', 'WARDEN')
def complaints_report_view(request):
    """Complaints Report: all issues by category and status."""
    export_format = request.GET.get('export')
    complaints = Complaint.objects.select_related('student', 'room', 'room__hostel').order_by('-created_at')

    if export_format in ['pdf', 'excel']:
        headers = ['ID', 'Student Name', 'Hostel/Room', 'Category', 'Title', 'Date Filed', 'Status', 'Remarks']
        rows = []
        for c in complaints:
            room_str = f"{c.room.hostel.name} Rm {c.room.room_no}" if c.room else "N/A"
            rows.append([
                f"#CMP-{c.pk}",
                c.student.name,
                room_str,
                c.get_category_display(),
                c.title,
                c.created_at.strftime('%Y-%m-%d'),
                c.get_status_display(),
                c.warden_remarks or 'None'
            ])

        if export_format == 'pdf':
            return generate_pdf_table_report("Complaints & Maintenance Report", headers, rows, filename="Complaints_Report.pdf")
        else:
            return generate_excel_table_report("Complaints & Maintenance Report", headers, rows, filename="Complaints_Report.xlsx")

    return render(request, 'reports/complaints_report.html', {'complaints': complaints})
