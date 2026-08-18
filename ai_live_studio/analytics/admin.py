from django.contrib import admin

from analytics.models import DailyUsage


@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'streams_count', 'watch_time_seconds', 'credits_used', 'peak_active_sessions')
    list_filter = ('date',)
    search_fields = ('user__username',)
    date_hierarchy = 'date'
