from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import student_required, warden_required, role_required
from .models import Complaint
from .forms import ComplaintSubmitForm, ComplaintUpdateForm
from allocations.models import Allocation
from notifications.utils import create_notification


@login_required
@student_required
def student_complaints_view(request):
    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    active_allocation = Allocation.objects.filter(student=student, is_active=True).first()
    complaints = student.complaints.all()

    if request.method == 'POST':
        form = ComplaintSubmitForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = student
            if active_allocation:
                complaint.room = active_allocation.room
            complaint.save()

            messages.success(request, f"Complaint #{complaint.pk} submitted. The hostel warden has been notified.")
            return redirect('student_complaints')
    else:
        form = ComplaintSubmitForm()

    return render(request, 'complaints/student_complaints.html', {
        'form': form,
        'complaints': complaints,
        'active_allocation': active_allocation
    })


@login_required
@warden_required
def warden_complaints_view(request):
    complaints = Complaint.objects.select_related('student', 'room', 'room__hostel').all()

    status = request.GET.get('status')
    category = request.GET.get('category')
    q = request.GET.get('q', '').strip()

    if status:
        complaints = complaints.filter(status=status)
    if category:
        complaints = complaints.filter(category=category)
    if q:
        complaints = complaints.filter(
            title__icontains=q
        ) | complaints.filter(student__name__icontains=q) | complaints.filter(description__icontains=q)

    return render(request, 'complaints/warden_complaints.html', {
        'complaints': complaints,
        'selected_status': status,
        'selected_category': category,
        'q': q
    })


@login_required
@warden_required
def warden_complaint_update_view(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            comp = form.save(commit=False)
            if comp.status in [Complaint.STATUS_RESOLVED, Complaint.STATUS_CLOSED]:
                comp.resolved_at = timezone.now()
                comp.resolved_by = request.user
            comp.save()

            create_notification(
                user=comp.student.user,
                title=f"Complaint #{comp.pk} Status: {comp.get_status_display()}",
                message=f"Your complaint '{comp.title}' has been updated to {comp.get_status_display()}. Remarks: {comp.warden_remarks or 'None'}",
                link='/complaints/student/'
            )

            messages.success(request, f"Complaint #{comp.pk} updated.")
            return redirect('warden_complaints')
    else:
        form = ComplaintUpdateForm(instance=complaint)

    return render(request, 'complaints/complaint_update.html', {
        'complaint': complaint,
        'form': form
    })
