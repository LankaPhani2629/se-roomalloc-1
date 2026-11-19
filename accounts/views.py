import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
import secrets
from .models import User, FacultyProfile, WardenProfile
from .forms import StudentRegistrationForm, LoginForm, StaffLoginForm, StaffCreationForm
from .decorators import role_required, admin_required, student_required
from applications.models import Student
from hostels.models import Hostel

security_logger = logging.getLogger('accounts.security')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # 1. Check account lockout
            target_user = User.objects.filter(username=username).first()
            if target_user and target_user.is_locked:
                minutes_left = max(1, int((target_user.locked_until - timezone.now()).total_seconds() // 60))
                security_logger.warning(f"Login attempted on locked user '{username}' from IP {request.META.get('REMOTE_ADDR')}")
                messages.error(request, f"Account is temporarily locked due to multiple failed login attempts. Please try again in {minutes_left} minute(s).")
                return render(request, 'accounts/login.html', {'form': form})

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    # Reset failed attempts
                    if user.failed_login_attempts > 0 or user.locked_until:
                        user.failed_login_attempts = 0
                        user.locked_until = None
                        user.save(update_fields=['failed_login_attempts', 'locked_until'])

                    security_logger.info(f"Successful login for user '{user.username}' (Role: {user.role})")
                    login(request, user)

                    if user.is_first_login:
                        messages.warning(request, "First login detected: You must change your temporary password to continue.")
                        return redirect('change_password')

                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    next_url = request.GET.get('next')
                    # Validate next_url against allowed host to prevent Open Redirect attacks
                    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)
                    return redirect('dashboard_redirect')
                else:
                    security_logger.warning(f"Login attempt on inactive account '{username}'")
                    messages.error(request, "This account is inactive. Please contact the administrator.")
            else:
                # Increment failed attempts
                if target_user:
                    target_user.failed_login_attempts += 1
                    max_attempts = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)
                    lockout_mins = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)
                    if target_user.failed_login_attempts >= max_attempts:
                        target_user.locked_until = timezone.now() + timezone.timedelta(minutes=lockout_mins)
                        security_logger.warning(f"Account '{username}' locked for {lockout_mins} mins after {target_user.failed_login_attempts} failed attempts.")
                        messages.error(request, f"Account locked for {lockout_mins} minutes due to repeated failed login attempts.")
                    else:
                        remaining = max_attempts - target_user.failed_login_attempts
                        security_logger.warning(f"Failed login attempt {target_user.failed_login_attempts}/{max_attempts} for user '{username}'")
                        messages.error(request, f"Invalid username or password. {remaining} attempt(s) remaining before temporary lockout.")
                    target_user.save(update_fields=['failed_login_attempts', 'locked_until'])
                else:
                    security_logger.warning(f"Failed login attempt for non-existent user '{username}'")
                    messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def staff_login_view(request):
    """
    Dedicated Staff Login portal for Administrators, Wardens, Faculty/HOD, and Accountants.
    Includes brute-force lockout, open redirect guard, and role validation.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Check account lockout
            target_user = User.objects.filter(username=username).first()
            if target_user and target_user.is_locked:
                minutes_left = max(1, int((target_user.locked_until - timezone.now()).total_seconds() // 60))
                security_logger.warning(f"Staff login attempted on locked user '{username}'")
                messages.error(request, f"Staff account is locked due to repeated failed attempts. Please retry in {minutes_left} minute(s).")
                return render(request, 'accounts/staff_login.html', {'form': form})

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.role == User.ROLE_STUDENT:
                    security_logger.warning(f"Student '{username}' attempted login via staff portal.")
                    messages.error(request, "Student accounts must use the Student Portal to sign in.")
                    return redirect('login')

                if user.is_active:
                    # Reset failed attempts
                    if user.failed_login_attempts > 0 or user.locked_until:
                        user.failed_login_attempts = 0
                        user.locked_until = None
                        user.save(update_fields=['failed_login_attempts', 'locked_until'])

                    security_logger.info(f"Staff login successful: '{user.username}' ({user.get_role_display()})")
                    login(request, user)

                    if user.is_first_login:
                        messages.warning(request, "First login detected: Please set your permanent password before accessing the staff portal.")
                        return redirect('change_password')

                    messages.success(request, f"Welcome, {user.first_name or user.username} ({user.get_role_display()})!")
                    next_url = request.GET.get('next')
                    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)
                    return redirect('dashboard_redirect')
                else:
                    security_logger.warning(f"Inactive staff login attempt: '{username}'")
                    messages.error(request, "Your staff account has been deactivated. Please contact the System Administrator.")
            else:
                if target_user:
                    target_user.failed_login_attempts += 1
                    max_attempts = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)
                    lockout_mins = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)
                    if target_user.failed_login_attempts >= max_attempts:
                        target_user.locked_until = timezone.now() + timezone.timedelta(minutes=lockout_mins)
                        security_logger.warning(f"Staff account '{username}' locked for {lockout_mins} mins.")
                        messages.error(request, f"Account locked for {lockout_mins} minutes due to repeated failed login attempts.")
                    else:
                        remaining = max_attempts - target_user.failed_login_attempts
                        security_logger.warning(f"Failed staff login attempt {target_user.failed_login_attempts}/{max_attempts} for '{username}'")
                        messages.error(request, f"Invalid staff credentials. {remaining} attempt(s) remaining.")
                    target_user.save(update_fields=['failed_login_attempts', 'locked_until'])
                else:
                    security_logger.warning(f"Failed staff login for unknown user '{username}'")
                    messages.error(request, "Invalid staff credentials. Check your employee username and password.")
    else:
        form = StaffLoginForm()

    return render(request, 'accounts/staff_login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You may now sign in to apply for hostel rooms.")
            return redirect('login')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def change_password_view(request):
    """Allows users to change their password; clears is_first_login flag on success."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            if user.is_first_login:
                user.is_first_login = False
                user.save(update_fields=['is_first_login'])
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully! You may now continue.")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def dashboard_redirect_view(request):
    """Redirect to role-specific dashboard after login."""
    if request.user.is_first_login:
        messages.warning(request, "You must change your initial temporary password before accessing the system.")
        return redirect('change_password')

    role = request.user.role
    if request.user.is_superuser or role == User.ROLE_ADMIN:
        return redirect('admin_dashboard')
    elif role == User.ROLE_WARDEN:
        return redirect('warden_dashboard')
    elif role == User.ROLE_FACULTY:
        return redirect('faculty_dashboard')
    elif role == User.ROLE_STUDENT:
        return redirect('student_dashboard')
    elif role == User.ROLE_ACCOUNTANT:
        return redirect('accountant_dashboard')
    return redirect('home')


# ==========================================
# STAFF MANAGEMENT (ADMINISTRATOR ONLY)
# ==========================================

@login_required
@admin_required
def admin_staff_list_view(request):
    """Administrator page to list, filter, and manage staff accounts."""
    staff_users = User.objects.exclude(role=User.ROLE_STUDENT).select_related('faculty_profile', 'warden_profile').order_by('role', 'username')
    
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_q = request.GET.get('q', '').strip()

    if role_filter:
        staff_users = staff_users.filter(role=role_filter)
    if status_filter == 'active':
        staff_users = staff_users.filter(is_active=True)
    elif status_filter == 'inactive':
        staff_users = staff_users.filter(is_active=False)
    if search_q:
        staff_users = staff_users.filter(username__icontains=search_q) | staff_users.filter(first_name__icontains=search_q) | staff_users.filter(email__icontains=search_q)

    return render(request, 'accounts/staff_list.html', {
        'staff_users': staff_users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_q': search_q,
    })


@login_required
@admin_required
def admin_add_staff_view(request):
    """Administrator page to provision a new staff account (Faculty, Warden, Accountant)."""
    temp_password = None
    created_user = None

    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            created_user, temp_password = form.save()
            messages.success(request, f"Staff account for {created_user.first_name} ({created_user.get_role_display()}) created successfully!")
            return render(request, 'accounts/staff_created_success.html', {
                'created_user': created_user,
                'temp_password': temp_password,
            })
    else:
        form = StaffCreationForm()

    return render(request, 'accounts/staff_add.html', {'form': form})


@login_required
@admin_required
def admin_staff_toggle_active_view(request, user_id):
    """Toggle active/deactivated status for a staff account."""
    staff_user = get_object_or_404(User, pk=user_id)
    if staff_user == request.user:
        messages.error(request, "You cannot deactivate your own administrator account.")
        return redirect('admin_staff_list')

    staff_user.is_active = not staff_user.is_active
    staff_user.save(update_fields=['is_active'])
    status_str = "activated" if staff_user.is_active else "deactivated"
    messages.success(request, f"Staff account for {staff_user.username} has been {status_str}.")
    return redirect('admin_staff_list')


@login_required
@admin_required
def admin_staff_reset_password_view(request, user_id):
    """Generate a new temporary password for a staff member and flag for first-login reset."""
    staff_user = get_object_or_404(User, pk=user_id)
    new_temp_pwd = secrets.token_urlsafe(8)
    staff_user.set_password(new_temp_pwd)
    staff_user.is_first_login = True
    staff_user.save(update_fields=['password', 'is_first_login'])

    messages.success(request, f"Password reset for {staff_user.username}. Temporary password: {new_temp_pwd}")
    return render(request, 'accounts/staff_password_reset_success.html', {
        'staff_user': staff_user,
        'new_temp_pwd': new_temp_pwd
    })


@login_required
@admin_required
def admin_staff_reassign_view(request, user_id):
    """Reassign hostel for wardens or department/designation for faculty."""
    staff_user = get_object_or_404(User, pk=user_id)
    hostels = Hostel.objects.all()

    if request.method == 'POST':
        if staff_user.role == User.ROLE_WARDEN and hasattr(staff_user, 'warden_profile'):
            hostel_id = request.POST.get('assigned_hostel')
            hostel = Hostel.objects.filter(pk=hostel_id).first() if hostel_id else None
            staff_user.warden_profile.assigned_hostel = hostel
            staff_user.warden_profile.save(update_fields=['assigned_hostel'])
            if hostel:
                hostel.warden = staff_user
                hostel.save(update_fields=['warden'])
            messages.success(request, f"Assigned hostel updated for {staff_user.username}.")
        elif staff_user.role == User.ROLE_FACULTY and hasattr(staff_user, 'faculty_profile'):
            dept = request.POST.get('department', '').strip()
            desig = request.POST.get('designation', '').strip()
            if dept:
                staff_user.faculty_profile.department = dept
                staff_user.faculty_profile.designation = desig
                staff_user.faculty_profile.save(update_fields=['department', 'designation'])
                messages.success(request, f"Faculty department/designation updated for {staff_user.username}.")
        return redirect('admin_staff_list')

    return render(request, 'accounts/staff_reassign.html', {
        'staff_user': staff_user,
        'hostels': hostels,
    })


@login_required
@admin_required
def admin_student_list_view(request):
    """Admin view to view and search students."""
    students = Student.objects.select_related('user').all()
    q = request.GET.get('q', '').strip()
    gender = request.GET.get('gender', '')
    year = request.GET.get('year', '')

    if q:
        students = students.filter(
            name__icontains=q
        ) | students.filter(student_id__icontains=q) | students.filter(email__icontains=q)
    if gender:
        students = students.filter(gender=gender)
    if year:
        students = students.filter(year=year)

    return render(request, 'accounts/student_list.html', {
        'students': students,
        'q': q,
        'gender': gender,
        'year': year,
    })
