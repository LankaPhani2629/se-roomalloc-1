from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from accounts.decorators import accountant_required, student_required, role_required
from .models import FeeStructure, FeePayment
from .forms import FeeStructureForm, RecordPaymentForm
from allocations.models import Allocation
from notifications.utils import create_notification


@login_required
@role_required('ACCOUNTANT', 'ADMIN')
def fee_structures_view(request):
    structures = FeeStructure.objects.all()

    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure saved successfully.")
            return redirect('fee_structures')
    else:
        form = FeeStructureForm()

    return render(request, 'fees/fee_structures.html', {
        'structures': structures,
        'form': form
    })


@login_required
@role_required('ACCOUNTANT', 'ADMIN')
def record_payment_view(request):
    alloc_id = request.GET.get('allocation')
    initial_alloc = None
    if alloc_id:
        initial_alloc = Allocation.objects.filter(pk=alloc_id, is_active=True).first()

    if request.method == 'POST':
        form = RecordPaymentForm(request.POST)
        if form.is_valid():
            allocation = form.cleaned_data['allocation']
            amount = form.cleaned_data['amount']
            payment_mode = form.cleaned_data['payment_mode']
            transaction_id = form.cleaned_data['transaction_id']
            remarks = form.cleaned_data['remarks']
            today = timezone.now().date()

            with transaction.atomic():
                # Check business rule: Confirmed only if paid by due date; otherwise Expired
                if today > allocation.due_date:
                    # Due date passed! Mark allotment Expired and decrement room occupancy
                    room = allocation.room
                    if room.occupied_count > 0:
                        room.occupied_count -= 1
                        room.save()

                    allocation.status = Allocation.STATUS_EXPIRED
                    allocation.is_active = False
                    allocation.save()

                    create_notification(
                        user=allocation.student.user,
                        title="Allotment Expired (Fee Overdue)",
                        message=f"Your room allotment for Room {room.room_no} has expired because fee payment was not made by the due date ({allocation.due_date}).",
                        link='/allocations/status/'
                    )
                    messages.error(
                        request,
                        f"Payment rejected! Due date ({allocation.due_date}) has expired. Allotment marked as EXPIRED and room released."
                    )
                    return redirect('pending_dues')

                # Paid on or before due date: Mark Confirmed
                receipt_no = FeePayment.generate_receipt_no()
                payment = FeePayment.objects.create(
                    allocation=allocation,
                    amount=amount,
                    payment_mode=payment_mode,
                    transaction_id=transaction_id,
                    receipt_no=receipt_no,
                    recorded_by=request.user,
                    remarks=remarks,
                    status=FeePayment.STATUS_SUCCESS
                )

                allocation.status = Allocation.STATUS_CONFIRMED
                if not allocation.check_in_date:
                    allocation.check_in_date = today
                allocation.save()

                create_notification(
                    user=allocation.student.user,
                    title="Fee Payment Successful & Allotment Confirmed",
                    message=f"Payment of ₹{amount} received (Receipt #{receipt_no}). Your room allotment is now CONFIRMED!",
                    link=f'/fees/receipt/{payment.pk}/'
                )

                messages.success(request, f"Payment recorded successfully! Receipt #{receipt_no} generated.")
                return redirect('receipt_detail', pk=payment.pk)
    else:
        initial_data = {}
        if initial_alloc:
            initial_data['allocation'] = initial_alloc
            # Find fee structure for this room type
            fee_struct = FeeStructure.objects.filter(
                room_type=initial_alloc.room.room_type,
                academic_year=initial_alloc.academic_year
            ).first()
            if fee_struct:
                initial_data['amount'] = fee_struct.amount

        form = RecordPaymentForm(initial=initial_data)

    return render(request, 'fees/record_payment.html', {
        'form': form,
        'initial_alloc': initial_alloc
    })


@login_required
@role_required('ACCOUNTANT', 'ADMIN')
def pending_dues_view(request):
    """List pending dues and allow batch expiry of overdue allocations."""
    today = timezone.now().date()
    pending_allocations = Allocation.objects.select_related(
        'student', 'room', 'room__hostel'
    ).filter(
        status=Allocation.STATUS_PENDING_PAYMENT,
        is_active=True
    ).order_by('due_date')

    # Handle batch expiry trigger
    if request.method == 'POST' and 'expire_overdue' in request.POST:
        overdue_allocs = pending_allocations.filter(due_date__lt=today)
        count = 0
        with transaction.atomic():
            for alloc in overdue_allocs:
                room = alloc.room
                if room.occupied_count > 0:
                    room.occupied_count -= 1
                    room.save()
                alloc.status = Allocation.STATUS_EXPIRED
                alloc.is_active = False
                alloc.save()
                count += 1
                create_notification(
                    user=alloc.student.user,
                    title="Room Allotment Expired",
                    message=f"Your room allotment in {room.hostel.name} has expired due to unpaid fee past the due date.",
                    link='/allocations/status/'
                )
        messages.info(request, f"Expired {count} overdue allotment(s) and released rooms.")
        return redirect('pending_dues')

    return render(request, 'fees/pending_dues.html', {
        'pending_allocations': pending_allocations,
        'today': today
    })


@login_required
@role_required('ACCOUNTANT', 'ADMIN')
def payment_history_view(request):
    payments = FeePayment.objects.select_related('allocation', 'allocation__student', 'recorded_by').all()
    q = request.GET.get('q', '').strip()
    if q:
        payments = payments.filter(
            receipt_no__icontains=q
        ) | payments.filter(transaction_id__icontains=q) | payments.filter(allocation__student__name__icontains=q)

    return render(request, 'fees/payment_history.html', {
        'payments': payments,
        'q': q
    })


@login_required
def receipt_detail_view(request, pk):
    payment = get_object_or_404(FeePayment.objects.select_related(
        'allocation', 'allocation__student', 'allocation__room', 'allocation__room__hostel'
    ), pk=pk)

    # Permission check: Student can only view their own receipt; Staff can view all
    if request.user.role == 'STUDENT':
        if not hasattr(request.user, 'student_profile') or payment.allocation.student != request.user.student_profile:
            messages.error(request, "Access denied.")
            return redirect('home')

    return render(request, 'fees/receipt_detail.html', {'payment': payment})


@login_required
@student_required
def student_fees_view(request):
    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    active_allocation = Allocation.objects.filter(student=student, is_active=True).first()
    payments = FeePayment.objects.filter(allocation__student=student).order_by('-payment_date')

    expected_fee = None
    if active_allocation:
        fee_struct = FeeStructure.objects.filter(
            room_type=active_allocation.room.room_type,
            academic_year=active_allocation.academic_year
        ).first()
        if fee_struct:
            expected_fee = fee_struct.amount

    return render(request, 'fees/student_fees.html', {
        'student': student,
        'allocation': active_allocation,
        'payments': payments,
        'expected_fee': expected_fee,
        'today': timezone.now().date()
    })
