from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from core.context_processors import get_telegram_support_url


def cookies_view(request):
    return render(request, 'pages/cookies.html')


def terms_view(request):
    return render(request, 'pages/terms.html')


def privacy_view(request):
    return render(request, 'pages/privacy.html')


def disclaimer_view(request):
    return render(request, 'pages/disclaimer.html')


def refund_policy_view(request):
    return render(request, 'pages/refund_policy.html')


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_body = request.POST.get('message', '').strip()

        if name and email and message_body:
            # Redirect the user straight to the Telegram DM so there is no bot
            # token or backend email configuration required.
            return redirect(get_telegram_support_url())

        messages.error(request, 'Please fill in all fields.')
        return redirect('pages:contact')
    return render(request, 'pages/contact.html')
