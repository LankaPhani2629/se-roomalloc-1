from django.contrib import admin
from .models import Hostel, Room


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostel_type', 'total_rooms', 'warden', 'created_at')
    list_filter = ('hostel_type',)
    search_fields = ('name', 'warden__username', 'warden__first_name', 'warden__last_name')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_no', 'hostel', 'floor_no', 'room_type', 'capacity', 'occupied_count', 'status', 'vacancy')
    list_filter = ('hostel', 'floor_no', 'room_type', 'status')
    search_fields = ('room_no', 'hostel__name')
