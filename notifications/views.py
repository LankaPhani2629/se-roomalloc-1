from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification


@login_required
def notifications_list_view(request):
    notifications = request.user.notifications.all()
    # Mark all as read when visited
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications
    })


@login_required
def mark_as_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications_list')


@login_required
def mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER', 'notifications_list'))
