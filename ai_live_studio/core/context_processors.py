from django.conf import settings


def site_context(request):
    """Global template variables available on every page."""
    context = {
        'SITE_NAME': settings.SITE_NAME,
        'AI_ENGINE_CONNECTED': settings.AI_ENGINE_CONNECTED,
    }

    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            context['unread_notifications_count'] = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications_count'] = 0

    return context
