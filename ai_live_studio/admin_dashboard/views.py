from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from broadcast.models import EmailBroadcast
from core.emails import send_deposit_approved_email, send_deposit_rejected_email
from core.utils import log_activity
from payments.models import CreditPlan, PaymentMethod, PaymentSubmission, PlatformSetting, Transaction
from studio.models import Stream

staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
@staff_required
def overview_view(request):
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(has_active_access=True).count(),
        'pending_payments': PaymentSubmission.objects.filter(status='pending').count(),
        'total_streams': Stream.objects.filter(started_at__isnull=False).count(),
        'live_now': Stream.objects.filter(status='live').count(),
        'recent_payments': PaymentSubmission.objects.select_related('user', 'plan')[:5],
    }
    return render(request, 'admin_dashboard/overview.html', context)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@login_required
@staff_required
def users_view(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.all()
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query) | Q(full_name__icontains=query)
        )

    paginator = Paginator(users, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard/users.html', {'page_obj': page_obj, 'query': query})


@login_required
@staff_required
@require_POST
def create_user_view(request):
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')

    if not username or not email or not password:
        messages.error(request, 'Username, email, and password are all required.')
        return redirect('admin_dashboard:users')

    if User.objects.filter(username=username).exists():
        messages.error(request, 'That username is already taken.')
        return redirect('admin_dashboard:users')

    user = User.objects.create_user(username=username, email=email, password=password)
    user.has_active_access = True  # admin-created users skip the payment gate
    user.is_email_verified = True
    user.save()
    log_activity(request, request.user, 'other', f'Admin created user "{username}"')
    messages.success(request, f'User "{username}" created.')
    return redirect('admin_dashboard:users')


@login_required
@staff_required
@require_POST
def edit_user_credits_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)

    credits_delta = request.POST.get('credits_delta', '').strip()
    plan_label = request.POST.get('plan_label', '').strip()
    note = request.POST.get('note', '').strip()

    if credits_delta:
        try:
            target.credits = max(0, target.credits + int(credits_delta))
            target.save(update_fields=['credits'])
        except ValueError:
            messages.error(request, 'Credits must be a whole number.')
            return redirect('admin_dashboard:users')

    if plan_label:
        target.subscription_plan = plan_label[:20]
        target.save(update_fields=['subscription_plan'])

    if not target.has_active_access:
        target.has_active_access = True
        target.save(update_fields=['has_active_access'])

    if credits_delta and int(credits_delta) != 0:
        Transaction.objects.create(
            user=target, amount=0, status='completed', method='credits_purchase',
            description=note or f'Admin adjustment: {credits_delta} credits',
            credits_awarded=max(0, int(credits_delta)),
        )

    log_activity(request, request.user, 'other', f'Admin adjusted credits for "{target.username}" by {credits_delta}')
    messages.success(request, f'Updated {target.username}.')
    return redirect('admin_dashboard:users')


@login_required
@staff_required
@require_POST
def suspend_user_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    target.account_status = 'suspended' if target.account_status != 'suspended' else 'active'
    target.is_active = target.account_status != 'suspended'
    target.save(update_fields=['account_status', 'is_active'])
    messages.success(request, f'{target.username} is now {target.account_status}.')
    return redirect('admin_dashboard:users')


@login_required
@staff_required
@require_POST
def delete_user_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        messages.error(request, "You can't delete a superuser from here.")
        return redirect('admin_dashboard:users')
    username = target.username
    target.delete()
    messages.success(request, f'{username} has been deleted.')
    return redirect('admin_dashboard:users')


# ---------------------------------------------------------------------------
# Credit Plans
# ---------------------------------------------------------------------------

@login_required
@staff_required
def plans_view(request):
    plans = CreditPlan.objects.all()
    return render(request, 'admin_dashboard/plans.html', {'plans': plans})


@login_required
@staff_required
@require_POST
def save_plan_view(request, plan_id=None):
    plan = get_object_or_404(CreditPlan, pk=plan_id) if plan_id else CreditPlan()
    plan.name = request.POST.get('name', '').strip()
    plan.price = request.POST.get('price') or 0
    plan.credits = request.POST.get('credits') or 0
    plan.minutes_label = request.POST.get('minutes_label', '').strip()
    plan.description = request.POST.get('description', '').strip()
    plan.is_active = bool(request.POST.get('is_active'))
    plan.order = request.POST.get('order') or 0
    plan.save()
    messages.success(request, f'Plan "{plan.name}" saved.')
    return redirect('admin_dashboard:plans')


@login_required
@staff_required
@require_POST
def delete_plan_view(request, plan_id):
    plan = get_object_or_404(CreditPlan, pk=plan_id)
    plan.delete()
    messages.success(request, 'Plan deleted.')
    return redirect('admin_dashboard:plans')


# ---------------------------------------------------------------------------
# Payment Methods (banks + crypto)
# ---------------------------------------------------------------------------

@login_required
@staff_required
def payment_methods_view(request):
    methods = PaymentMethod.objects.all()
    return render(request, 'admin_dashboard/payment_methods.html', {'methods': methods})


@login_required
@staff_required
@require_POST
def save_payment_method_view(request, method_id=None):
    method = get_object_or_404(PaymentMethod, pk=method_id) if method_id else PaymentMethod()
    method.method_type = request.POST.get('method_type', 'bank')
    method.bank_name = request.POST.get('bank_name', '').strip()
    method.account_name = request.POST.get('account_name', '').strip()
    method.account_number = request.POST.get('account_number', '').strip()
    method.routing_or_swift = request.POST.get('routing_or_swift', '').strip()
    method.crypto_currency = request.POST.get('crypto_currency', '').strip()
    method.wallet_address = request.POST.get('wallet_address', '').strip()
    method.network_note = request.POST.get('network_note', '').strip()
    method.is_active = bool(request.POST.get('is_active'))
    method.order = request.POST.get('order') or 0
    method.save()
    messages.success(request, 'Payment method saved.')
    return redirect('admin_dashboard:payment_methods')


@login_required
@staff_required
@require_POST
def delete_payment_method_view(request, method_id):
    method = get_object_or_404(PaymentMethod, pk=method_id)
    method.delete()
    messages.success(request, 'Payment method deleted.')
    return redirect('admin_dashboard:payment_methods')


# ---------------------------------------------------------------------------
# Payment Submissions (approve / reject)
# ---------------------------------------------------------------------------

@login_required
@staff_required
def payment_submissions_view(request):
    status_filter = request.GET.get('status', 'pending')
    submissions = PaymentSubmission.objects.select_related('user', 'plan', 'method')
    if status_filter != 'all':
        submissions = submissions.filter(status=status_filter)
    return render(request, 'admin_dashboard/payment_submissions.html', {
        'submissions': submissions,
        'status_filter': status_filter,
    })


@login_required
@staff_required
@require_POST
def approve_payment_view(request, submission_id):
    submission = get_object_or_404(PaymentSubmission, pk=submission_id)
    submission.status = 'approved'
    submission.reviewed_by = request.user
    submission.reviewed_at = timezone.now()
    submission.save()

    target = submission.user
    is_first_approval = not target.has_active_access  # capture before flipping the flag

    if submission.plan:
        target.credits += submission.plan.credits
        target.subscription_plan = submission.plan.name[:20]
    target.has_active_access = True
    target.save()

    Transaction.objects.create(
        user=target, amount=submission.amount, status='completed', method=submission.method.method_type if submission.method else 'bank_transfer',
        description=f'Approved payment for {submission.plan.name if submission.plan else "plan"}',
        credits_awarded=submission.plan.credits if submission.plan else 0,
    )

    # Referral bonus: the referrer earns bonus credits the moment their
    # referred user's FIRST payment is approved (not on later top-ups).
    if is_first_approval and target.referred_by:
        referrer = target.referred_by
        referrer.add_credits(settings.REFERRAL_BONUS_CREDITS)
        Transaction.objects.create(
            user=referrer, amount=0, status='completed', method='credits_purchase',
            description=f'Referral bonus — {target.username} completed their first payment',
            credits_awarded=settings.REFERRAL_BONUS_CREDITS,
        )
        log_activity(request, request.user, 'other', f'Referral bonus of {settings.REFERRAL_BONUS_CREDITS} credits awarded to {referrer.username}')

    log_activity(request, request.user, 'other', f'Approved payment #{submission.id} for {target.username}')
    send_deposit_approved_email(submission)
    messages.success(request, f'Approved — {target.username} now has {target.credits} credits.')
    return redirect('admin_dashboard:payment_submissions')


@login_required
@staff_required
@require_POST
def reject_payment_view(request, submission_id):
    submission = get_object_or_404(PaymentSubmission, pk=submission_id)
    submission.status = 'rejected'
    submission.admin_note = request.POST.get('note', '').strip()
    submission.reviewed_by = request.user
    submission.reviewed_at = timezone.now()
    submission.save()
    send_deposit_rejected_email(submission)
    messages.success(request, 'Payment rejected.')
    return redirect('admin_dashboard:payment_submissions')


# ---------------------------------------------------------------------------
# Platform Settings (Decart key)
# ---------------------------------------------------------------------------

@login_required
@staff_required
def platform_settings_view(request):
    setting = PlatformSetting.load()
    return render(request, 'admin_dashboard/platform_settings.html', {'setting': setting})


@login_required
@staff_required
@require_POST
def save_platform_settings_view(request):
    setting = PlatformSetting.load()
    setting.decart_api_key_override = request.POST.get('decart_api_key', '').strip()
    setting.support_telegram_username = request.POST.get('telegram_support_username', '').strip()
    setting.save()
    messages.success(request, 'Platform settings updated.')
    return redirect('admin_dashboard:platform_settings')
