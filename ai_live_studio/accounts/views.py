from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.forms import (
    ForgotPasswordForm, LoginForm, ProfileForm, RegisterForm, SetNewPasswordForm,
)
from accounts.models import EmailVerificationToken, PasswordResetToken, User
from core.emails import send_welcome_email
from core.utils import log_activity


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.full_name = form.cleaned_data['full_name']
            user.country = form.cleaned_data.get('country', '')
            user.credits = 0  # credits are granted once an admin approves a payment

            ref_code = (request.POST.get('ref') or request.GET.get('ref') or '').strip()
            if ref_code:
                referrer = User.objects.filter(referral_code=ref_code).first()
                if referrer and referrer.id != user.id:
                    user.referred_by = referrer

            user.save()

            token = EmailVerificationToken.objects.create(user=user)
            _send_verification_email(request, user, token)

            log_activity(request, user, 'register', 'New account created')
            messages.success(
                request,
                'Account created! Please check your email to verify your account '
                '(in dev mode, check the console output for the link).'
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form, 'ref_code': request.GET.get('ref', '')})


def _send_verification_email(request, user, token):
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', args=[token.token])
    )
    send_welcome_email(user, verify_url)


def verify_email_view(request, token):
    verification = EmailVerificationToken.objects.filter(token=token).first()
    if verification and verification.is_valid():
        verification.used = True
        verification.save(update_fields=['used'])
        user = verification.user
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        messages.success(request, 'Your email has been verified. You can now log in.')
    else:
        messages.error(request, 'This verification link is invalid or has expired.')
    return redirect('accounts:login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_activity(request, user, 'login', 'User logged in')
            messages.success(request, f'Welcome back, {user.display_name}!')
            next_url = request.GET.get('next')
            return redirect(next_url or 'dashboard:home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    log_activity(request, request.user, 'logout', 'User logged out')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            if user:
                token = PasswordResetToken.objects.create(user=user)
                reset_url = request.build_absolute_uri(
                    reverse('accounts:reset_password', args=[token.token])
                )
                send_mail(
                    subject='Reset your AI Live Studio password',
                    message=f'Reset your password by visiting:\n{reset_url}\n\n'
                            f'This link expires in 1 hour. If you didn\'t request this, ignore this email.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            # Always show the same message to avoid leaking which emails exist
            messages.success(
                request,
                'If an account with that email exists, a reset link has been sent.'
            )
            return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    if not reset_token.is_valid():
        messages.error(request, 'This reset link is invalid or has expired.')
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['password1'])
            user.save()
            reset_token.used = True
            reset_token.save(update_fields=['used'])
            messages.success(request, 'Your password has been reset. Please log in.')
            return redirect('accounts:login')
    else:
        form = SetNewPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})


def _stylize_form(form):
    for field in form.fields.values():
        existing = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = (existing + ' form-control').strip()
    return form


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed.')
            return redirect('dashboard:settings')
        _stylize_form(form)
    else:
        form = _stylize_form(PasswordChangeForm(request.user))

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(request, request.user, 'profile_update', 'Profile updated')
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
