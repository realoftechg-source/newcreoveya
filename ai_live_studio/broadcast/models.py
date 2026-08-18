from django.conf import settings
from django.db import models


class EmailBroadcast(models.Model):
    """
    One row per admin-triggered bulk email. Created immediately when an
    admin hits "Send to All Users", then updated in place (by
    broadcast.services.send_bulk_email, running in a background thread) as
    batches complete, so the dashboard can show live-ish progress and a
    permanent history of what was sent, when, and how it went.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('completed_with_errors', 'Completed with errors'),
        ('failed', 'Failed'),
    ]

    subject = models.CharField(max_length=200)
    message = models.TextField(help_text='Plain-text body sent to every recipient.')

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='broadcasts_sent'
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    sandbox_mode = models.BooleanField(
        default=False, help_text='If True, this was a SendGrid sandbox (dry-run) send — nothing was actually delivered.'
    )

    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Broadcast'
        verbose_name_plural = 'Email Broadcasts'

    def __str__(self):
        return f'{self.subject} ({self.get_status_display()})'

    @property
    def progress_percent(self):
        if not self.total_recipients:
            return 0
        return int(((self.sent_count + self.failed_count) / self.total_recipients) * 100)
