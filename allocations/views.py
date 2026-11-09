from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.decorators import admin_required, warden_required, student_required, role_required
from applications.models import Student, Application
from hostels.models import Room, Hostel
from .models import Allocation, RoomChangeRequest, AllocationRule
from .forms import AllocationRuleForm, ManualAllocationForm, RoomChangeRequestForm, ProcessRoomRequestForm
from .services import allocate_room_to_student, run_automatic_allocation, process_room_change_or_vacate


@login_required
@admin_required
def allocation_rules_view(request):
    rules = AllocationRule.objects.all()

    if request.method == 'POST':
        form = AllocationRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Allocation rule created successfully.")
            return redirect('allocation_rules')
    else:
        form = AllocationRuleForm()

    return render(request, 'allocations/allocation_rules.html', {
        'rules': rules,
        'form': form
    })


@login_required
@admin_required
def delete_allocation_rule_view(request, pk):
    rule = get_object_or_404(AllocationRule, pk=pk)
    rule.delete()
    messages.success(request, f"Rule '{rule.name}' deleted.")
    return redirect('allocation_rules')


@login_required
@admin_required
def run_auto_allocation_view(request):
    if request.method == 'POST':
        academic_year = request.POST.get('academic_year')
        outcome = run_automatic_allocation(academic_year=academic_year)
        return render(request, 'allocations/auto_allocation_result.html', {
            'outcome': outcome,
            'academic_year': academic_year or 'All Years'
        })
    return render(request, 'allocations/auto_allocation_confirm.html')


@login_required
@warden_required
def manual_allocation_view(request):
    if request.method == 'POST':
        form = ManualAllocationForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            room = form.cleaned_data['room']
            due_days = form.cleaned_data['due_days']
            try:
                alloc = allocate_room_to_student(student=student, room=room, due_days=due_days)
                messages.success(
                    request,
                    f"Room {room.room_no} in {room.hostel.name} manually allocated to {student.name}. Due date: {alloc.due_date}."
                )
                return redirect('allocation_results')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = ManualAllocationForm()

    return render(request, 'allocations/manual_allocation.html', {'form': form})


@login_required
@role_required('ADMIN', 'WARDEN', 'ACCOUNTANT')
def allocation_results_view(request):
    """View all allotments with search and filters."""
    allocations = Allocation.objects.select_related('student', 'room', 'room__hostel').all()

    hostel_id = request.GET.get('hostel')
    status = request.GET.get('status')
    q = request.GET.get('q', '').strip()

    if hostel_id:
        allocations = allocations.filter(room__hostel_id=hostel_id)
    if status:
        allocations = allocations.filter(status=status)
    if q:
        allocations = allocations.filter(
            student__name__icontains=q
        ) | allocations.filter(student__student_id__icontains=q) | allocations.filter(room__room_no__icontains=q)

    hostels = Hostel.objects.all()
    return render(request, 'allocations/allocation_results.html', {
        'allocations': allocations,
        'hostels': hostels,
        'selected_hostel': hostel_id,
        'selected_status': status,
        'q': q,
    })


@login_required
@student_required
def student_room_detail_view(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    active_allocation = Allocation.objects.select_related('room', 'room__hostel').filter(
        student=student,
        is_active=True
    ).first()

    roommates = []
    if active_allocation:
        roommates = Allocation.objects.select_related('student').filter(
            room=active_allocation.room,
            is_active=True
        ).exclude(student=student)

    return render(request, 'allocations/student_room_detail.html', {
        'student': student,
        'allocation': active_allocation,
        'roommates': roommates
    })


@login_required
@student_required
def student_room_requests_view(request):
    """Student submits room change or vacating request, views history."""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    active_allocation = Allocation.objects.filter(student=student, is_active=True).first()
    requests_history = student.room_change_requests.all()

    if request.method == 'POST':
        if not active_allocation:
            messages.error(request, "You cannot request a room change or vacation without an active room allotment.")
            return redirect('student_room_requests')

        form = RoomChangeRequestForm(request.POST)
        if form.is_valid():
            req_obj = form.save(commit=False)
            req_obj.student = student
            req_obj.current_allocation = active_allocation
            req_obj.save()

            messages.success(request, f"Your {req_obj.get_request_type_display()} has been submitted to the warden for review.")
            return redirect('student_room_requests')
    else:
        form = RoomChangeRequestForm()

    return render(request, 'allocations/student_room_requests.html', {
        'form': form,
        'active_allocation': active_allocation,
        'requests_history': requests_history
    })


@login_required
@warden_required
def warden_room_requests_view(request):
    requests_list = RoomChangeRequest.objects.select_related(
        'student', 'current_allocation', 'current_allocation__room', 'target_room'
    ).all()

    status = request.GET.get('status')
    req_type = request.GET.get('type')

    if status:
        requests_list = requests_list.filter(status=status)
    if req_type:
        requests_list = requests_list.filter(request_type=req_type)

    return render(request, 'allocations/warden_room_requests.html', {
        'requests_list': requests_list,
        'selected_status': status,
        'selected_type': req_type
    })


@login_required
@warden_required
def warden_process_request_view(request, pk):
    req_obj = get_object_or_404(RoomChangeRequest, pk=pk)

    if request.method == 'POST':
        form = ProcessRoomRequestForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            target_room = form.cleaned_data['target_room']
            remarks = form.cleaned_data['remarks']

            try:
                process_room_change_or_vacate(
                    change_request=req_obj,
                    warden_user=request.user,
                    decision=decision,
                    remarks=remarks,
                    target_room=target_room
                )
                messages.success(request, f"Request #{req_obj.pk} processed as {decision}.")
                return redirect('warden_room_requests')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = ProcessRoomRequestForm(initial={'decision': req_obj.status if req_obj.status != 'PENDING' else 'APPROVED'})
        # Filter rooms to gender-matched
        target_gender = 'BOYS' if req_obj.student.gender == Student.GENDER_MALE else 'GIRLS'
        form.fields['target_room'].queryset = Room.objects.filter(
            hostel__hostel_type=target_gender,
            status=Room.STATUS_AVAILABLE
        ).exclude(pk=req_obj.current_allocation.room_id)

    return render(request, 'allocations/process_request.html', {
        'req_obj': req_obj,
        'form': form
    })
