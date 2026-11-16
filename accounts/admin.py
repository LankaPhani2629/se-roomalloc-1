from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FacultyProfile, WardenProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_first_login', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'is_first_login')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Security', {'fields': ('role', 'phone', 'is_first_login')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Security', {'fields': ('role', 'phone', 'is_first_login')}),
    )


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'department', 'designation', 'phone', 'email')
    search_fields = ('employee_id', 'name', 'department', 'email')
    list_filter = ('department', 'designation')


@admin.register(WardenProfile)
class WardenProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'phone', 'assigned_hostel')
    search_fields = ('employee_id', 'name', 'phone')
    list_filter = ('assigned_hostel',)
