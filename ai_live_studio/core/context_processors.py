from django.conf import settings

from payments.models import PlatformSetting


def get_telegram_support_url():
    username = (PlatformSetting.load().support_telegram_username or '').strip()
    if username:
        return f'https://t.me/{username.lstrip("@")}'

    env_username = (getattr(settings, 'TELEGRAM_SUPPORT_USERNAME', '') or '').strip()
    if env_username:
        return f'https://t.me/{env_username.lstrip("@")}'

    return getattr(settings, 'TELEGRAM_SUPPORT_URL', 'https://t.me/')


def site_context(request):
    """Global template variables available on every page."""
    setting = PlatformSetting.load()
    telegram_username = (setting.support_telegram_username or '').strip()
    context = {
        'SITE_NAME': settings.SITE_NAME,
        'AI_ENGINE_CONNECTED': settings.AI_ENGINE_CONNECTED,
        'TELEGRAM_SUPPORT_USERNAME': telegram_username or getattr(settings, 'TELEGRAM_SUPPORT_USERNAME', ''),
        'TELEGRAM_SUPPORT_URL': get_telegram_support_url(),
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
