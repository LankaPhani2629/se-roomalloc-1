from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import admin_required, role_required
from .models import Hostel, Room
from .forms import HostelForm, RoomForm


@login_required
@admin_required
def hostel_list_view(request):
    hostels = Hostel.objects.all().prefetch_related('rooms')
    return render(request, 'hostels/hostel_list.html', {'hostels': hostels})


@login_required
@admin_required
def hostel_create_view(request):
    if request.method == 'POST':
        form = HostelForm(request.POST)
        if form.is_valid():
            hostel = form.save()
            messages.success(request, f"Hostel '{hostel.name}' added successfully.")
            return redirect('hostel_list')
    else:
        form = HostelForm()
    return render(request, 'hostels/hostel_form.html', {'form': form, 'title': 'Add New Hostel'})


@login_required
@admin_required
def hostel_update_view(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    if request.method == 'POST':
        form = HostelForm(request.POST, instance=hostel)
        if form.is_valid():
            form.save()
            messages.success(request, f"Hostel '{hostel.name}' updated successfully.")
            return redirect('hostel_list')
    else:
        form = HostelForm(instance=hostel)
    return render(request, 'hostels/hostel_form.html', {'form': form, 'title': f'Edit Hostel: {hostel.name}', 'hostel': hostel})


@login_required
@admin_required
def hostel_delete_view(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    if request.method == 'POST':
        if hostel.total_occupied > 0:
            messages.error(request, f"Cannot delete hostel '{hostel.name}' because it currently has occupied rooms.")
            return redirect('hostel_list')
        name = hostel.name
        hostel.delete()
        messages.success(request, f"Hostel '{name}' deleted successfully.")
        return redirect('hostel_list')
    return render(request, 'hostels/hostel_confirm_delete.html', {'hostel': hostel})


@login_required
@role_required('ADMIN', 'WARDEN')
def room_list_view(request):
    """List rooms with filters (hostel, floor, room type, status) and search."""
    rooms = Room.objects.select_related('hostel').all()

    # Filter parameters
    hostel_id = request.GET.get('hostel')
    floor_no = request.GET.get('floor')
    room_type = request.GET.get('room_type')
    status = request.GET.get('status')
    q = request.GET.get('q', '').strip()

    if hostel_id:
        rooms = rooms.filter(hostel_id=hostel_id)
    if floor_no:
        rooms = rooms.filter(floor_no=floor_no)
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if status:
        rooms = rooms.filter(status=status)
    if q:
        rooms = rooms.filter(room_no__icontains=q)

    hostels = Hostel.objects.all()
    # Unique floors for filter dropdown
    floors = Room.objects.values_list('floor_no', flat=True).distinct().order_by('floor_no')

    return render(request, 'hostels/room_list.html', {
        'rooms': rooms,
        'hostels': hostels,
        'floors': floors,
        'selected_hostel': hostel_id,
        'selected_floor': floor_no,
        'selected_room_type': room_type,
        'selected_status': status,
        'q': q,
    })


@login_required
@admin_required
def room_create_view(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"Room {room.room_no} in {room.hostel.name} created successfully.")
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'hostels/room_form.html', {'form': form, 'title': 'Add New Room'})


@login_required
@admin_required
def room_update_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Room {room.room_no} updated successfully.")
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hostels/room_form.html', {'form': form, 'title': f'Edit Room {room.room_no}', 'room': room})


@login_required
@admin_required
def room_delete_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        if room.occupied_count > 0:
            messages.error(request, f"Cannot delete room {room.room_no} because it currently has {room.occupied_count} occupant(s).")
            return redirect('room_list')
        hostel = room.hostel
        room_no = room.room_no
        room.delete()
        hostel.update_room_count()
        messages.success(request, f"Room {room_no} deleted successfully.")
        return redirect('room_list')
    return render(request, 'hostels/room_confirm_delete.html', {'room': room})
