from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Generic audit trail of user activity across the platform."""

    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Register'),
        ('stream_start', 'Stream Started'),
        ('stream_stop', 'Stream Stopped'),
        ('credits_purchase', 'Credits Purchased'),
        ('plan_change', 'Plan Changed'),
        ('profile_update', 'Profile Updated'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='activity_logs', null=True, blank=True,
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, default='other')
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f'{self.user} - {self.get_action_display()} @ {self.created_at:%Y-%m-%d %H:%M}'
