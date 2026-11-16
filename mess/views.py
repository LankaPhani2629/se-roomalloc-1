from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta
from accounts.decorators import role_required, warden_required, accountant_required, student_required
from .models import MessMenu, MessAttendance, MessFeedback, MessFee
from hostels.models import Hostel
from applications.models import Student


@login_required
def mess_menu_view(request):
    """View active hostel mess menus for the current week."""
    today = timezone.now().date()
    menus = MessMenu.objects.filter(date__gte=today).order_by('date', 'meal')[:14]
    
    # If student, fetch their skipped meals for the week
    skipped_meal_keys = set()
    if request.user.is_student and hasattr(request.user, 'student_profile'):
        skips = MessAttendance.objects.filter(
            student=request.user.student_profile,
            date__gte=today,
            is_skipped=True
        )
        for s in skips:
            skipped_meal_keys.add(f"{s.date}_{s.meal}")

    return render(request, 'mess/menu_view.html', {
        'menus': menus,
        'today': today,
        'skipped_meal_keys': skipped_meal_keys,
    })


@login_required
@warden_required
def mess_menu_publish_view(request):
    """Warden or Mess In-Charge publishes a meal menu."""
    hostels = Hostel.objects.all()
    if request.method == 'POST':
        hostel_id = request.POST.get('hostel')
        menu_date = request.POST.get('date')
        meal = request.POST.get('meal')
        items = request.POST.get('items', '').strip()

        hostel = Hostel.objects.filter(pk=hostel_id).first()
        if hostel and menu_date and meal and items:
            MessMenu.objects.update_or_create(
                hostel=hostel,
                date=menu_date,
                meal=meal,
                defaults={'items': items, 'published_by': request.user}
            )
            messages.success(request, f"Menu for {meal} on {menu_date} published successfully.")
            return redirect('mess_menu')
        else:
            messages.error(request, "Please enter all required menu details.")

    return render(request, 'mess/menu_publish.html', {
        'hostels': hostels,
        'meal_choices': MessMenu.MEAL_CHOICES,
    })


@login_required
@student_required
def mess_skip_meal_view(request):
    """Student flags a meal to skip before the cutoff time to claim a meal rebate."""
    student = request.user.student_profile
    if request.method == 'POST':
        date_str = request.POST.get('date')
        meal = request.POST.get('meal')
        action = request.POST.get('action', 'skip') # 'skip' or 'attend'

        if date_str and meal:
            is_skipped = (action == 'skip')
            MessAttendance.objects.update_or_create(
                student=student,
                date=date_str,
                meal=meal,
                defaults={'is_skipped': is_skipped}
            )
            msg = "Meal marked as skipped (rebate eligible)." if is_skipped else "Meal marked as attending."
            messages.success(request, msg)
    return redirect('mess_menu')


@login_required
@student_required
def mess_feedback_view(request):
    """Student rates and reviews today's meal (1-5 stars)."""
    student = request.user.student_profile
    if request.method == 'POST':
        meal = request.POST.get('meal')
        rating = int(request.POST.get('rating', 5))
        comments = request.POST.get('comments', '').strip()

        if meal:
            MessFeedback.objects.create(
                student=student,
                date=timezone.now().date(),
                meal=meal,
                rating=rating,
                comments=comments
            )
            messages.success(request, "Thank you for your rating & feedback on the mess meal!")
            return redirect('mess_menu')

    return render(request, 'mess/feedback.html', {'meal_choices': MessMenu.MEAL_CHOICES})


@login_required
@accountant_required
def mess_billing_view(request):
    """Accountant generates monthly mess bills with rebates for skipped meals."""
    students = Student.objects.filter(allocations__is_active=True).distinct()
    bills = MessFee.objects.select_related('student').order_by('-year', '-month')

    if request.method == 'POST':
        month = int(request.POST.get('month', timezone.now().month))
        year = int(request.POST.get('year', timezone.now().year))
        base_fee = float(request.POST.get('base_amount', 4500.00))
        rebate_per_meal = float(request.POST.get('rebate_per_meal', 40.00))

        generated_count = 0
        for student in students:
            # Calculate skipped meals in this month
            skipped_count = MessAttendance.objects.filter(
                student=student,
                date__year=year,
                date__month=month,
                is_skipped=True
            ).count()

            rebate_total = round(skipped_count * rebate_per_meal, 2)
            total = max(0.0, base_fee - rebate_total)

            MessFee.objects.update_or_create(
                student=student,
                month=month,
                year=year,
                defaults={
                    'base_amount': base_fee,
                    'skipped_meals_count': skipped_count,
                    'rebate_amount': rebate_total,
                    'total_amount': total,
                }
            )
            generated_count += 1

        messages.success(request, f"Generated {generated_count} monthly mess bills for {month}/{year}.")
        return redirect('mess_billing')

    return render(request, 'mess/billing.html', {
        'bills': bills[:25],
        'current_month': timezone.now().month,
        'current_year': timezone.now().year,
    })


@login_required
def mess_reports_view(request):
    """Analytics on mess expenditure, food wastage trends, and meal satisfaction ratings."""
    avg_ratings = MessFeedback.objects.values('meal').annotate(avg_rating=Avg('rating'), count=Count('id'))
    total_skipped = MessAttendance.objects.filter(is_skipped=True).count()
    recent_feedbacks = MessFeedback.objects.select_related('student').order_by('-created_at')[:10]

    return render(request, 'mess/reports.html', {
        'avg_ratings': avg_ratings,
        'total_skipped': total_skipped,
        'recent_feedbacks': recent_feedbacks,
    })
