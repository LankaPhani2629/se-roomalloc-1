from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .models import User
from .forms import StudentRegistrationForm, LoginForm
from .decorators import role_required, admin_required
from applications.models import Student


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('dashboard_redirect')
                else:
                    messages.error(request, "This account is inactive. Please contact the administrator.")
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


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
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def dashboard_redirect_view(request):
    """Redirect to role-specific dashboard after login."""
    role = request.user.role
    if request.user.is_superuser or role == User.ROLE_ADMIN:
        return redirect('admin_dashboard')
    elif role == User.ROLE_WARDEN:
        return redirect('warden_dashboard')
    elif role == User.ROLE_STUDENT:
        return redirect('student_dashboard')
    elif role == User.ROLE_ACCOUNTANT:
        return redirect('accountant_dashboard')
    return redirect('home')


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
