from django.contrib import admin
from .models import Allocation, RoomChangeRequest, AllocationRule


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'room', 'academic_year', 'allocation_date', 'due_date', 'status', 'is_active')
    list_filter = ('status', 'is_active', 'academic_year', 'room__hostel')
    search_fields = ('student__student_id', 'student__name', 'room__room_no', 'room__hostel__name')


@admin.register(RoomChangeRequest)
class RoomChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'request_type', 'current_allocation', 'target_room', 'status', 'created_at')
    list_filter = ('request_type', 'status')
    search_fields = ('student__student_id', 'student__name')


@admin.register(AllocationRule)
class AllocationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority_order', 'gender', 'year_of_study', 'room_type', 'merit_weight', 'is_active')
    list_filter = ('is_active', 'gender')
