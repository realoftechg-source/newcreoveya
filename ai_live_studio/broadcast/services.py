"""
Bulk email sending via SendGrid's official Python library (not Django's
built-in email backend / not django-anymail — see the README for why:
in short, anymail's SendGrid support has been unofficially deprecated,
so this goes straight to SendGrid's own, actively-maintained client).

Runs in a background thread (kicked off from broadcast.views.send_broadcast_view)
so the admin's HTTP request returns immediately instead of blocking on
however long it takes to email every user.
"""

import logging

from django.conf import settings
from django.utils import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, MailSettings, SandBoxMode

logger = logging.getLogger(__name__)


def _chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def send_bulk_email(broadcast_id):
    """
    Sends broadcast.subject / broadcast.message to every active user's
    email address, in batches, updating the EmailBroadcast row after each
    batch so progress survives a crash mid-send and the dashboard can
    poll for live status.
    """
    # Imported here (not at module level) to avoid a circular import
    # between broadcast.models and accounts.models at app-loading time.
    from accounts.models import User
    from broadcast.models import EmailBroadcast

    broadcast = EmailBroadcast.objects.get(pk=broadcast_id)
    broadcast.status = 'sending'
    broadcast.sandbox_mode = settings.BROADCAST_SANDBOX_MODE
    broadcast.save(update_fields=['status', 'sandbox_mode'])

    if not settings.SENDGRID_API_KEY:
        broadcast.status = 'failed'
        broadcast.error_log = 'SENDGRID_API_KEY is not configured — see .env / Render environment variables.'
        broadcast.completed_at = timezone.now()
        broadcast.save(update_fields=['status', 'error_log', 'completed_at'])
        logger.error('Broadcast %s failed: SENDGRID_API_KEY not set', broadcast_id)
        return

    recipient_emails = list(
        User.objects.filter(is_active=True)
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )

    broadcast.total_recipients = len(recipient_emails)
    broadcast.save(update_fields=['total_recipients'])

    if not recipient_emails:
        broadcast.status = 'completed'
        broadcast.completed_at = timezone.now()
        broadcast.save(update_fields=['status', 'completed_at'])
        logger.info('Broadcast %s: no recipients found, nothing to send.', broadcast_id)
        return

    sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    sent_count = 0
    failed_count = 0
    errors = []

    for batch in _chunk(recipient_emails, settings.BROADCAST_BATCH_SIZE):
        try:
            mail = Mail(
                from_email=settings.BROADCAST_FROM_EMAIL,
                to_emails=batch,
                subject=broadcast.subject,
                plain_text_content=broadcast.message,
                is_multiple=True,  # separate personalization per recipient —
                                   # no one in the batch sees anyone else's address
            )

            if settings.BROADCAST_SANDBOX_MODE:
                mail_settings = MailSettings()
                mail_settings.sandbox_mode = SandBoxMode(True)
                mail.mail_settings = mail_settings

            response = sg_client.send(mail)

            # Sandbox mode returns 200 on a valid dry run; a real send
            # returns 202 once SendGrid has accepted it for delivery.
            if response.status_code in (200, 202):
                sent_count += len(batch)
            else:
                failed_count += len(batch)
                error_msg = f'Batch of {len(batch)} failed — status {response.status_code}: {response.body}'
                errors.append(error_msg)
                logger.error('Broadcast %s: %s', broadcast_id, error_msg)

        except Exception as exc:
            failed_count += len(batch)
            errors.append(f'Batch of {len(batch)} raised an exception: {exc}')
            logger.exception('Broadcast %s: batch send raised an exception', broadcast_id)

        # Persist progress after every batch — so a crash mid-send doesn't
        # lose the counts, and the dashboard can poll for live progress.
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.error_log = '\n'.join(errors)[-8000:]  # keep the log bounded
        broadcast.save(update_fields=['sent_count', 'failed_count', 'error_log'])

    broadcast.status = 'completed' if failed_count == 0 else 'completed_with_errors'
    broadcast.completed_at = timezone.now()
    broadcast.save(update_fields=['status', 'completed_at'])

    logger.info(
        'Broadcast %s finished: %s sent, %s failed, sandbox=%s',
        broadcast_id, sent_count, failed_count, settings.BROADCAST_SANDBOX_MODE,
    )
