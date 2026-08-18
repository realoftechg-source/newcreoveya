from django.contrib import admin

from studio.models import Look, Stream, WebRTCSession


@admin.register(Look)
class LookAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'user', 'status', 'look', 'quality',
        'resolution', 'audience_count', 'credits_used', 'created_at',
    )
    list_filter = ('status', 'quality', 'resolution')
    search_fields = ('title', 'user__username', 'stream_id')
    readonly_fields = ('stream_id', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(WebRTCSession)
class WebRTCSessionAdmin(admin.ModelAdmin):
    list_display = ('viewer_id', 'stream', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    readonly_fields = ('viewer_id', 'created_at', 'updated_at')
