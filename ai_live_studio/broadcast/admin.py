import threading

from django import forms
from django.contrib import admin, messages

from accounts.models import User
from broadcast.models import EmailBroadcast
from broadcast.services import send_bulk_email

READONLY_AFTER_SEND = [
    'subject', 'message', 'sent_by', 'status', 'sandbox_mode',
    'total_recipients', 'sent_count', 'failed_count', 'error_log',
    'created_at', 'completed_at',
]


class EmailBroadcastAdminForm(forms.ModelForm):
    class Meta:
        model = EmailBroadcast
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={'style': 'width: 60%;'}),
            'message': forms.Textarea(attrs={'rows': 12, 'style': 'width: 60%;'}),
        }


@admin.register(EmailBroadcast)
class EmailBroadcastAdmin(admin.ModelAdmin):
    """
    Bulk email broadcasting, controlled exclusively from here — there is no
    separate dashboard page. Only superusers can see this section at all
    (regular staff, even with other admin access, cannot send broadcasts).

    Filling in the "Add Email Broadcast" form and clicking Save queues the
    send (via a background thread, see broadcast/services.py) — there's no
    other way to trigger one. Once created, a broadcast becomes read-only:
    you can watch its progress but never edit or resend it, since a send
    already in flight (or completed) shouldn't be altered.
    """

    form = EmailBroadcastAdminForm
    list_display = (
        'subject', 'sent_by', 'status', 'sandbox_mode',
        'total_recipients', 'sent_count', 'failed_count', 'created_at',
    )
    list_filter = ('status', 'sandbox_mode', 'created_at')
    search_fields = ('subject', 'message', 'sent_by__username')
    date_hierarchy = 'created_at'

    # --- Superuser-only, end to end ------------------------------------

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        # Viewing the detail page is allowed (to watch progress); actually
        # editing fields is not, enforced via get_readonly_fields below —
        # this stays True so the (read-only) detail page remains reachable.
        return bool(request.user.is_active and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    # --- Only subject/message are ever editable, and only before sending

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['subject', 'message']
        return READONLY_AFTER_SEND

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return READONLY_AFTER_SEND

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            count = User.objects.filter(is_active=True).exclude(email='').count()
            form.base_fields['subject'].help_text = (
                f'This will be sent to all {count} active registered users '
                f'with a saved email address.'
            )
        return form

    # --- Creating a row here is literally what triggers the send --------

    def save_model(self, request, obj, form, change):
        if change:
            return  # editing is blocked by has_change_permission/readonly fields; guard anyway

        obj.sent_by = request.user
        obj.status = 'pending'
        super().save_model(request, obj, form, change)

        thread = threading.Thread(target=send_bulk_email, args=(obj.id,), daemon=True)
        thread.start()

        messages.success(
            request,
            f'"{obj.subject}" queued — sending now in the background. '
            f'Refresh this page (or the list view) to see live progress.'
        )
