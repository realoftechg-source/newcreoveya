from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render


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
            try:
                send_mail(
                    subject=f'New contact form message from {name}',
                    message=f'From: {name} <{email}>\n\n{message_body}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_FORM_RECIPIENT],
                    fail_silently=False,
                )
                messages.success(request, "Thanks for reaching out — we'll get back to you soon.")
            except Exception:
                messages.error(request, "Sorry, something went wrong sending your message. Please try again shortly.")
        else:
            messages.error(request, 'Please fill in all fields.')

        return redirect('pages:contact')
    return render(request, 'pages/contact.html')
