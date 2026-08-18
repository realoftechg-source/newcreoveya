from django.conf import settings
from django.db import models


class DailyUsage(models.Model):
    """Daily rollup of a user's activity, used to power analytics charts."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_usage')
    date = models.DateField()
    streams_count = models.PositiveIntegerField(default=0)
    watch_time_seconds = models.PositiveIntegerField(default=0)
    credits_used = models.PositiveIntegerField(default=0)
    peak_active_sessions = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} - {self.date}'
