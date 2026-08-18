def get_client_ip(request):
    """Return the client's IP address, respecting a reverse proxy header."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_activity(request, user, action, description=''):
    """Create an ActivityLog entry. Import kept local to avoid app-loading
    order issues when called from other apps' views."""
    from core.models import ActivityLog

    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request) if request else None,
        path=request.path if request else '',
    )
