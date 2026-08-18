from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.emails import send_deposit_pending_email
from core.utils import log_activity
from payments.forms import PaymentSubmissionForm
from payments.models import CreditPlan, PaymentMethod, PaymentSubmission, Transaction


@login_required
def payment_gate_view(request):
    """
    Shown immediately after registering/logging in until an admin approves
    a payment (enforced by core/middleware.py's PaymentGateMiddleware).
    Already-approved users can also reach this page voluntarily (e.g. from
    the Credits page) to submit a top-up payment when they run low.
    """
    if request.user.is_staff:
        return redirect('dashboard:home')

    pending = PaymentSubmission.objects.filter(user=request.user, status='pending').select_related('plan', 'method').first()
    rejected = PaymentSubmission.objects.filter(user=request.user, status='rejected').select_related('plan').first()

    plans = CreditPlan.objects.filter(is_active=True)
    bank_methods = PaymentMethod.objects.filter(is_active=True, method_type='bank')
    crypto_methods = PaymentMethod.objects.filter(is_active=True, method_type='crypto')

    context = {
        'plans': plans,
        'bank_methods': bank_methods,
        'crypto_methods': crypto_methods,
        'pending': pending,
        'rejected': rejected,
    }
    return render(request, 'payments/payment_gate.html', context)


@login_required
@require_POST
def submit_payment_view(request):
    # Only one pending submission at a time
    if PaymentSubmission.objects.filter(user=request.user, status='pending').exists():
        messages.info(request, 'You already have a payment pending review.')
        return redirect('payments:gate')

    plan_id = request.POST.get('plan')
    method_id = request.POST.get('method')
    plan = get_object_or_404(CreditPlan, pk=plan_id, is_active=True)
    method = get_object_or_404(PaymentMethod, pk=method_id, is_active=True)

    form = PaymentSubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
        return redirect('payments:gate')

    submission = form.save(commit=False)
    submission.user = request.user
    submission.plan = plan
    submission.method = method
    submission.amount = plan.price
    submission.status = 'pending'
    submission.save()

    send_deposit_pending_email(submission)

    log_activity(request, request.user, 'other', f'Submitted payment for plan "{plan.name}"')
    messages.success(request, 'Payment submitted — an admin will review it shortly.')
    return redirect('payments:gate')


@login_required
def receipt_image_view(request, submission_id):
    """Private — only the submitting user or staff can view a receipt."""
    submission = get_object_or_404(PaymentSubmission, pk=submission_id)
    if submission.user_id != request.user.id and not request.user.is_staff:
        raise Http404
    return FileResponse(submission.receipt.open('rb'))


@login_required
def credits_view(request):
    plans = CreditPlan.objects.filter(is_active=True)
    return render(request, 'payments/credits.html', {'plans': plans})


@login_required
def billing_view(request):
    submissions = PaymentSubmission.objects.filter(user=request.user).select_related('plan')[:20]
    return render(request, 'payments/billing.html', {'submissions': submissions})


@login_required
def transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'payments/transactions.html', {'transactions': transactions})
