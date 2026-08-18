from django.contrib import admin

from core.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'description', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'user__email', 'description', 'ip_address')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'path', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
