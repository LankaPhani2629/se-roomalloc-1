def unread_notifications_processor(request):
    """Context processor providing unread notifications count and recent list."""
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False)
        return {
            'unread_notifications_count': unread_notifications.count(),
            'recent_notifications': request.user.notifications.all()[:5],
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

