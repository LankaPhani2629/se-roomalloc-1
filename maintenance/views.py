from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import role_required, warden_required, admin_required, student_required
from .models import MaintenanceRequest, MaintenanceStaff
from notifications.utils import create_notification


@login_required
def maintenance_list_view(request):
    """List maintenance requests scoped by user role."""
    user = request.user
    status_filter = request.GET.get('status', '')
    cat_filter = request.GET.get('category', '')
    prio_filter = request.GET.get('priority', '')

    if user.is_student:
        try:
            student = user.student_profile
            tickets = MaintenanceRequest.objects.filter(student=student)
        except Exception:
            tickets = MaintenanceRequest.objects.none()
    elif user.is_warden:
        assigned_hostel = getattr(user.warden_profile, 'assigned_hostel', None) if hasattr(user, 'warden_profile') else None
        if assigned_hostel:
            tickets = MaintenanceRequest.objects.filter(room__hostel=assigned_hostel)
        else:
            tickets = MaintenanceRequest.objects.all()
    else:  # Admin & others
        tickets = MaintenanceRequest.objects.all()

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if cat_filter:
        tickets = tickets.filter(category=cat_filter)
    if prio_filter:
        tickets = tickets.filter(priority=prio_filter)

    staff_members = MaintenanceStaff.objects.filter(active=True)

    return render(request, 'maintenance/maintenance_list.html', {
        'tickets': tickets.select_related('student', 'room', 'room__hostel', 'assigned_staff'),
        'staff_members': staff_members,
        'status_filter': status_filter,
        'cat_filter': cat_filter,
        'prio_filter': prio_filter,
    })


@login_required
@student_required
def maintenance_create_view(request):
    """Students raise maintenance tickets for their currently allotted room."""
    student = request.user.student_profile
    active_allocation = student.allocations.filter(is_active=True).first()

    if not active_allocation:
        messages.error(request, "You must hold an active hostel room allotment to report room maintenance issues.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        category = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', MaintenanceRequest.PRIO_MEDIUM)
        photo = request.FILES.get('photo')

        if not category or not description:
            messages.error(request, "Please fill in all mandatory fields.")
        else:
            ticket = MaintenanceRequest.objects.create(
                student=student,
                room=active_allocation.room,
                category=category,
                description=description,
                priority=priority,
                photo=photo,
                status=MaintenanceRequest.STATUS_OPEN
            )
            # Notify the hostel warden
            warden = active_allocation.room.hostel.warden
            if warden:
                create_notification(
                    user=warden,
                    title="New Maintenance Ticket",
                    message=f"Room {active_allocation.room.room_no} reported: {ticket.get_category_display()}",
                    link=f"/maintenance/request/{ticket.pk}/"
                )

            messages.success(request, f"Maintenance ticket #{ticket.pk} submitted successfully.")
            return redirect('maintenance_list')

    return render(request, 'maintenance/maintenance_create.html', {
        'student': student,
        'allocation': active_allocation,
        'categories': MaintenanceRequest.CATEGORY_CHOICES,
        'priorities': MaintenanceRequest.PRIORITY_CHOICES,
    })


@login_required
def maintenance_detail_view(request, pk):
    """View detailed ticket status, history, assigned staff, and resolution rating."""
    ticket = get_object_or_404(MaintenanceRequest.objects.select_related('student', 'room', 'assigned_staff'), pk=pk)
    staff_members = MaintenanceStaff.objects.filter(active=True)
    return render(request, 'maintenance/maintenance_detail.html', {
        'ticket': ticket,
        'staff_members': staff_members
    })


@login_required
@warden_required
def maintenance_update_status_view(request, pk):
    """Warden updates ticket status, assigns technician, or marks under maintenance."""
    ticket = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        staff_id = request.POST.get('assigned_staff')
        notes = request.POST.get('warden_notes', '').strip()
        res_notes = request.POST.get('resolution_notes', '').strip()
        mark_room_maint = request.POST.get('mark_room_maintenance') == 'on'

        if staff_id:
            ticket.assigned_staff = MaintenanceStaff.objects.filter(pk=staff_id).first()
        if notes:
            ticket.warden_notes = notes

        if new_status:
            ticket.status = new_status
            if new_status == MaintenanceRequest.STATUS_RESOLVED:
                ticket.resolved_at = timezone.now()
                ticket.resolution_notes = res_notes

        ticket.save()

        # If warden opted to mark room status as UNDER MAINTENANCE
        if mark_room_maint:
            ticket.room.status = 'MAINTENANCE'
            ticket.room.save(update_fields=['status'])

        # Notify student of update
        create_notification(
            user=ticket.student.user,
            title=f"Maintenance Ticket #{ticket.pk} Updated",
            message=f"Status: {ticket.get_status_display()}. {res_notes or notes}",
            link=f"/maintenance/request/{ticket.pk}/"
        )

        messages.success(request, f"Ticket #{ticket.pk} updated successfully.")
    return redirect('maintenance_detail', pk=pk)


@login_required
@student_required
def maintenance_rate_view(request, pk):
    """Student rates the resolved maintenance ticket (1-5 stars) or reopens it."""
    ticket = get_object_or_404(MaintenanceRequest, pk=pk, student=request.user.student_profile)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reopen':
            ticket.status = MaintenanceRequest.STATUS_REOPENED
            reopen_reason = request.POST.get('reopen_reason', '').strip()
            ticket.student_feedback = f"Reopened: {reopen_reason}"
            ticket.save(update_fields=['status', 'student_feedback'])
            messages.warning(request, f"Ticket #{ticket.pk} has been reopened.")
        else:
            rating = int(request.POST.get('rating', 5))
            feedback = request.POST.get('feedback', '').strip()
            ticket.rating = rating
            ticket.student_feedback = feedback
            ticket.status = MaintenanceRequest.STATUS_CLOSED
            ticket.save(update_fields=['rating', 'student_feedback', 'status'])
            messages.success(request, "Thank you for your rating and feedback!")
    return redirect('maintenance_detail', pk=pk)


@login_required
@admin_required
def maintenance_staff_manage_view(request):
    """Admin page to manage technicians, add staff, and view resolution analytics."""
    staff_members = MaintenanceStaff.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        spec = request.POST.get('specialization', '').strip()
        if name and phone and spec:
            MaintenanceStaff.objects.create(name=name, phone=phone, specialization=spec)
            messages.success(request, f"Maintenance technician {name} added.")
            return redirect('maintenance_staff_manage')
    return render(request, 'maintenance/staff_manage.html', {'staff_members': staff_members})
