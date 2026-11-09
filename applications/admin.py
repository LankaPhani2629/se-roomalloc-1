from django.contrib import admin
from .models import Student, ApplicationPeriod, Application


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'gender', 'course', 'year', 'phone', 'email', 'merit_score')
    list_filter = ('gender', 'year', 'course')
    search_fields = ('student_id', 'name', 'email', 'phone')


@admin.register(ApplicationPeriod)
class ApplicationPeriodAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'start_date', 'end_date', 'is_active', 'is_currently_open')
    list_filter = ('is_active', 'academic_year')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'academic_year', 'preferred_room_type', 'status', 'priority_score', 'application_date')
    list_filter = ('status', 'preferred_room_type', 'academic_year')
    search_fields = ('student__student_id', 'student__name')
