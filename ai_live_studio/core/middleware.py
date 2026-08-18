class ActivityLogMiddleware:
    """
    Lightweight middleware placeholder for future request-level activity
    tracking (e.g. rate limiting, audit trails). Currently a pass-through;
    explicit activity logs are written directly from views via
    core.utils.log_activity() to keep the log meaningful and low-noise.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


# Path prefixes that stay reachable even while a user hasn't been
# approved yet — the payment gate itself, auth (so they can log out),
# static/media, and both admin surfaces.
PAYMENT_GATE_EXEMPT_PREFIXES = (
    '/billing/',
    '/pages/',
    '/accounts/logout/',
    '/accounts/login/',
    '/accounts/register/',
    '/accounts/forgot-password/',
    '/accounts/reset-password/',
    '/accounts/verify-email/',
    '/admin/',
    '/admin_dashboard/',
    '/static/',
    '/media/',
)


class PaymentGateMiddleware:
    """
    Forces any logged-in, non-staff user who hasn't had a payment approved
    yet straight to the payment/plan-selection page — they can't reach the
    dashboard, studio, or anything else until an admin approves their
    first payment. Staff/superusers are never gated.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_staff
            and not getattr(user, 'has_active_access', True)
            and not request.path.startswith(PAYMENT_GATE_EXEMPT_PREFIXES)
        ):
            from django.shortcuts import redirect
            return redirect('payments:gate')

        return self.get_response(request)
