from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import student_required, warden_required, admin_required, role_required
from .models import Student, Application, ApplicationPeriod
from .forms import StudentProfileForm, RoomApplicationForm, ApplicationPeriodForm, ApplicationReviewForm
from notifications.utils import create_notification
from allocations.models import Allocation


@login_required
@student_required
def student_profile_view(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('home')

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated.")
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'applications/student_profile.html', {
        'student': student,
        'form': form
    })


@login_required
@student_required
def apply_room_view(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    # Check active allotment rule: student can have only one active allotment
    active_allocation = Allocation.objects.filter(student=student, is_active=True).first()
    if active_allocation:
        messages.warning(
            request,
            f"You already have an active room allocation in {active_allocation.room.hostel.name} (Room {active_allocation.room.room_no}). "
            "You cannot apply for a new room while holding an active allocation. Use the Room Change request instead."
        )
        return redirect('student_application_status')

    # Check if application period is open
    active_period = ApplicationPeriod.objects.filter(is_active=True).order_by('-start_date').first()
    today = timezone.now().date()
    is_open = active_period and (active_period.start_date <= today <= active_period.end_date)

    if not is_open:
        return render(request, 'applications/application_closed.html', {
            'active_period': active_period
        })

    # Check if existing pending or approved application exists for this academic year
    existing_app = Application.objects.filter(
        student=student,
        academic_year=active_period.academic_year,
        status__in=[Application.STATUS_PENDING, Application.STATUS_APPROVED, Application.STATUS_WAITLISTED]
    ).first()

    if existing_app:
        messages.info(
            request,
            f"You already submitted an application for academic year {active_period.academic_year}. Current status: {existing_app.get_status_display()}."
        )
        return redirect('student_application_status')

    if request.method == 'POST':
        form = RoomApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = student
            application.academic_year = active_period.academic_year
            application.status = Application.STATUS_PENDING
            # Base priority score is calculated based on merit score and year
            application.priority_score = int(student.merit_score) + (student.year * 5)
            application.save()

            # Create notification
            create_notification(
                user=request.user,
                title="Room Application Submitted",
                message=f"Your room application for {active_period.academic_year} ({application.get_preferred_room_type_display()}) was submitted successfully.",
                link='/applications/status/'
            )

            messages.success(request, "Your hostel room application has been submitted successfully!")
            return redirect('student_application_status')
    else:
        form = RoomApplicationForm()

    return render(request, 'applications/apply_room.html', {
        'form': form,
        'student': student,
        'active_period': active_period
    })


@login_required
@student_required
def student_application_status_view(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    applications = student.applications.all()
    active_allocation = Allocation.objects.filter(student=student, is_active=True).first()

    return render(request, 'applications/application_status.html', {
        'student': student,
        'applications': applications,
        'active_allocation': active_allocation
    })


@login_required
@warden_required
def warden_applications_view(request):
    """Wardens view applications with filters and can approve/reject."""
    applications = Application.objects.select_related('student', 'student__user').all()

    # Filters
    status = request.GET.get('status')
    room_type = request.GET.get('room_type')
    gender = request.GET.get('gender')
    q = request.GET.get('q', '').strip()

    if status:
        applications = applications.filter(status=status)
    if room_type:
        applications = applications.filter(preferred_room_type=room_type)
    if gender:
        applications = applications.filter(student__gender=gender)
    if q:
        applications = applications.filter(
            student__name__icontains=q
        ) | applications.filter(student__student_id__icontains=q)

    return render(request, 'applications/warden_applications.html', {
        'applications': applications,
        'selected_status': status,
        'selected_room_type': room_type,
        'selected_gender': gender,
        'q': q,
    })


@login_required
@warden_required
def warden_application_review_view(request, pk):
    application = get_object_or_404(Application, pk=pk)

    if request.method == 'POST':
        form = ApplicationReviewForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            remarks = form.cleaned_data['remarks']

            application.status = new_status
            application.remarks = remarks
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()

            # Create notification for student
            create_notification(
                user=application.student.user,
                title=f"Application {application.get_status_display()}",
                message=f"Your room application for {application.academic_year} has been marked as {application.get_status_display()}. Remarks: {remarks or 'None'}",
                link='/applications/status/'
            )

            messages.success(request, f"Application #{application.pk} for {application.student.name} marked as {application.get_status_display()}.")
            return redirect('warden_applications')
    else:
        form = ApplicationReviewForm(initial={
            'status': application.status if application.status in [Application.STATUS_APPROVED, Application.STATUS_WAITLISTED, Application.STATUS_REJECTED] else Application.STATUS_APPROVED,
            'remarks': application.remarks
        })

    return render(request, 'applications/application_review.html', {
        'application': application,
        'form': form
    })


@login_required
@admin_required
def application_periods_view(request):
    periods = ApplicationPeriod.objects.all()

    if request.method == 'POST':
        form = ApplicationPeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Application Period saved successfully.")
            return redirect('application_periods')
    else:
        form = ApplicationPeriodForm()

    return render(request, 'applications/application_periods.html', {
        'periods': periods,
        'form': form
    })
