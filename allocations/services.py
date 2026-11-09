import logging
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F

from applications.models import Student, Application
from hostels.models import Hostel, Room
from .models import Allocation, RoomChangeRequest, AllocationRule
from notifications.utils import create_notification

logger = logging.getLogger(__name__)


def calculate_application_priority(application):
    """
    Calculates priority score based on student merit score and configurable AllocationRules.
    """
    student = application.student
    score = int(student.merit_score) + (student.year * 5)

    rules = AllocationRule.objects.filter(is_active=True).order_by('priority_order')
    for rule in rules:
        matches_gender = (rule.gender == AllocationRule.GENDER_ALL or rule.gender == student.gender)
        matches_year = (rule.year_of_study is None or rule.year_of_study == student.year)
        matches_room_type = (not rule.room_type or rule.room_type == application.preferred_room_type)

        if matches_gender and matches_year and matches_room_type:
            score += rule.merit_weight

    application.priority_score = score
    application.save(update_fields=['priority_score'])
    return score


def allocate_room_to_student(student, room, application=None, due_days=7):
    """
    Allocates a room to a student atomically.
    Validates:
    - Gender-appropriate hostel (Boys only to Boys, Girls only to Girls)
    - Room capacity not exceeded
    - Only one active allotment per student
    """
    # Rule 1: Gender-appropriate hostel
    if student.gender == Student.GENDER_MALE and room.hostel.hostel_type != Hostel.TYPE_BOYS:
        raise ValidationError("Male students can only be allotted to Boys Hostels.")
    if student.gender == Student.GENDER_FEMALE and room.hostel.hostel_type != Hostel.TYPE_GIRLS:
        raise ValidationError("Female students can only be allotted to Girls Hostels.")

    # Rule 3: Single active allotment
    if Allocation.objects.filter(student=student, is_active=True).exists():
        raise ValidationError(f"Student {student.name} ({student.student_id}) already has an active room allotment.")

    with transaction.atomic():
        # Lock room row to prevent race conditions & double-booking
        locked_room = Room.objects.select_for_update().get(pk=room.pk)

        # Rule 2: Capacity check
        if locked_room.occupied_count >= locked_room.capacity:
            raise ValidationError(
                f"Room {locked_room.room_no} in {locked_room.hostel.name} has already reached capacity ({locked_room.capacity})."
            )

        # Calculate due date
        due_date = timezone.now().date() + timedelta(days=due_days)
        academic_year = application.academic_year if application else '2026-2027'

        allocation = Allocation.objects.create(
            student=student,
            room=locked_room,
            application=application,
            academic_year=academic_year,
            allocation_date=timezone.now().date(),
            due_date=due_date,
            status=Allocation.STATUS_PENDING_PAYMENT,
            is_active=True
        )

        # Increment occupied count
        locked_room.occupied_count += 1
        locked_room.save()

        # Update application status
        if application:
            application.status = Application.STATUS_APPROVED
            application.save(update_fields=['status'])

        # Notify student
        create_notification(
            user=student.user,
            title="Hostel Room Allocated!",
            message=(
                f"Congratulations! You have been allocated Room {locked_room.room_no} in {locked_room.hostel.name}. "
                f"Please pay the hostel fee by {due_date.strftime('%B %d, %Y')} to confirm your allotment."
            ),
            link='/allocations/my-room/'
        )

        return allocation


def run_automatic_allocation(academic_year=None):
    """
    Executes rule-based automatic allocation for pending/approved applications.
    Matches gender, room preferences, and priority scores inside DB transactions.
    """
    apps = Application.objects.select_related('student', 'student__user').filter(
        status__in=[Application.STATUS_PENDING, Application.STATUS_APPROVED],
        allocation__isnull=True
    )
    if academic_year:
        apps = apps.filter(academic_year=academic_year)

    # Recalculate priority scores
    for app in apps:
        calculate_application_priority(app)

    # Sort applications by priority score (descending), then by application date
    sorted_apps = list(apps.order_by('-priority_score', 'application_date'))

    allocated_count = 0
    unallocated_count = 0
    results = []

    for app in sorted_apps:
        student = app.student

        # Check if already has active allocation
        if Allocation.objects.filter(student=student, is_active=True).exists():
            continue

        target_hostel_type = Hostel.TYPE_BOYS if student.gender == Student.GENDER_MALE else Hostel.TYPE_GIRLS

        # Search for available room in gender-appropriate hostel matching preferred room type
        candidate_rooms = Room.objects.select_related('hostel').filter(
            hostel__hostel_type=target_hostel_type,
            room_type=app.preferred_room_type,
            status=Room.STATUS_AVAILABLE,
            occupied_count__lt=F('capacity')
        ).order_by('hostel__name', 'floor_no', 'room_no')

        allocated = False
        for room in candidate_rooms:
            try:
                alloc = allocate_room_to_student(student=student, room=room, application=app)
                allocated = True
                allocated_count += 1
                results.append({
                    'student': student.name,
                    'roll_id': student.student_id,
                    'hostel': room.hostel.name,
                    'room': room.room_no,
                    'status': 'Allocated',
                    'due_date': alloc.due_date
                })
                break
            except ValidationError:
                continue

        if not allocated:
            # Fallback: check any available room in gender-appropriate hostel
            fallback_rooms = Room.objects.select_related('hostel').filter(
                hostel__hostel_type=target_hostel_type,
                status=Room.STATUS_AVAILABLE,
                occupied_count__lt=F('capacity')
            ).order_by('hostel__name', 'floor_no', 'room_no')

            for room in fallback_rooms:
                try:
                    alloc = allocate_room_to_student(student=student, room=room, application=app)
                    allocated = True
                    allocated_count += 1
                    results.append({
                        'student': student.name,
                        'roll_id': student.student_id,
                        'hostel': room.hostel.name,
                        'room': room.room_no,
                        'status': 'Allocated (Fallback Room Type)',
                        'due_date': alloc.due_date
                    })
                    break
                except ValidationError:
                    continue

        if not allocated:
            unallocated_count += 1
            app.status = Application.STATUS_WAITLISTED
            app.remarks = "Waitlisted automatically due to room capacity shortage in gender hostel."
            app.save(update_fields=['status', 'remarks'])
            results.append({
                'student': student.name,
                'roll_id': student.student_id,
                'hostel': '-',
                'room': '-',
                'status': 'Waitlisted (No free room in hostel)',
                'due_date': '-'
            })

    return {
        'allocated_count': allocated_count,
        'unallocated_count': unallocated_count,
        'results': results
    }


def process_room_change_or_vacate(change_request, warden_user, decision, remarks='', target_room=None):
    """
    Atomically processes a student's room change or vacating request.
    Updates room occupancy counts and dates safely in transaction.
    """
    with transaction.atomic():
        req = RoomChangeRequest.objects.select_for_update().get(pk=change_request.pk)
        current_alloc = Allocation.objects.select_for_update().get(pk=req.current_allocation_id)
        current_room = Room.objects.select_for_update().get(pk=current_alloc.room_id)

        if decision == 'APPROVED':
            if req.request_type == RoomChangeRequest.TYPE_VACATE:
                # 1. Vacate request
                if current_room.occupied_count > 0:
                    current_room.occupied_count -= 1
                    current_room.save()

                current_alloc.status = Allocation.STATUS_VACATED
                current_alloc.is_active = False
                current_alloc.vacate_date = timezone.now().date()
                current_alloc.save()

                req.status = RoomChangeRequest.STATUS_APPROVED
                req.warden_remarks = remarks
                req.actioned_by = warden_user
                req.actioned_at = timezone.now()
                req.save()

                create_notification(
                    user=req.student.user,
                    title="Vacate Request Approved",
                    message=f"Your room vacating request for Room {current_room.room_no} has been approved. Room vacated.",
                    link='/allocations/requests/'
                )

            elif req.request_type == RoomChangeRequest.TYPE_CHANGE:
                # 2. Room change request
                new_room = target_room or req.target_room
                if not new_room:
                    raise ValidationError("A target room must be specified for room change approval.")

                new_room_locked = Room.objects.select_for_update().get(pk=new_room.pk)

                # Validate gender match
                if req.student.gender == Student.GENDER_MALE and new_room_locked.hostel.hostel_type != Hostel.TYPE_BOYS:
                    raise ValidationError("Male students can only be moved to Boys Hostels.")
                if req.student.gender == Student.GENDER_FEMALE and new_room_locked.hostel.hostel_type != Hostel.TYPE_GIRLS:
                    raise ValidationError("Female students can only be moved to Girls Hostels.")

                # Validate capacity
                if new_room_locked.occupied_count >= new_room_locked.capacity:
                    raise ValidationError(f"Target Room {new_room_locked.room_no} has no vacant capacity.")

                # Decrement old room
                if current_room.occupied_count > 0:
                    current_room.occupied_count -= 1
                    current_room.save()

                # Increment new room
                new_room_locked.occupied_count += 1
                new_room_locked.save()

                # Vacate old allocation
                current_alloc.is_active = False
                current_alloc.status = Allocation.STATUS_VACATED
                current_alloc.vacate_date = timezone.now().date()
                current_alloc.save()

                # Create new active allocation for target room
                Allocation.objects.create(
                    student=req.student,
                    room=new_room_locked,
                    academic_year=current_alloc.academic_year,
                    allocation_date=timezone.now().date(),
                    check_in_date=timezone.now().date(),
                    due_date=timezone.now().date() + timedelta(days=7),
                    status=Allocation.STATUS_CONFIRMED,
                    is_active=True
                )

                req.status = RoomChangeRequest.STATUS_APPROVED
                req.warden_remarks = remarks
                req.target_room = new_room_locked
                req.actioned_by = warden_user
                req.actioned_at = timezone.now()
                req.save()

                create_notification(
                    user=req.student.user,
                    title="Room Change Approved!",
                    message=f"Your room change request has been approved. You are now allotted Room {new_room_locked.room_no} in {new_room_locked.hostel.name}.",
                    link='/allocations/my-room/'
                )

        elif decision == 'REJECTED':
            req.status = RoomChangeRequest.STATUS_REJECTED
            req.warden_remarks = remarks
            req.actioned_by = warden_user
            req.actioned_at = timezone.now()
            req.save()

            create_notification(
                user=req.student.user,
                title=f"{req.get_request_type_display()} Rejected",
                message=f"Your request was rejected by the warden. Remarks: {remarks or 'None'}",
                link='/allocations/requests/'
            )

        return req
