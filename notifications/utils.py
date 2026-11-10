import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


def create_notification(user, title, message, link=''):
    """
    Creates an in-app notification record and sends an email via console backend.
    """
    # 1. In-app notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link
    )

    # 2. Console email backend notification
    if user.email:
        try:
            send_mail(
                subject=f"[Hostel Portal] {title}",
                message=f"Hello {user.get_full_name() or user.username},\n\n{message}\n\nView details: {link}\n\nHostel Administration",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'hostel-admin@college.edu'),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Failed to send email notification to {user.email}: {e}")

    return notification

