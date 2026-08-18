from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import EmailVerificationToken, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 'subscription_plan',
        'credits', 'account_status', 'is_email_verified', 'date_joined',
    )
    list_filter = ('subscription_plan', 'account_status', 'is_email_verified', 'is_staff')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('full_name', 'country', 'avatar', 'bio')}),
        ('Platform', {'fields': ('credits', 'subscription_plan', 'account_status', 'is_email_verified')}),
    )

    actions = ['add_100_credits', 'suspend_accounts', 'activate_accounts']

    @admin.action(description='Add 100 credits to selected users')
    def add_100_credits(self, request, queryset):
        for user in queryset:
            user.add_credits(100)

    @admin.action(description='Suspend selected accounts')
    def suspend_accounts(self, request, queryset):
        queryset.update(account_status='suspended')

    @admin.action(description='Activate selected accounts')
    def activate_accounts(self, request, queryset):
        queryset.update(account_status='active')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used')
    readonly_fields = ('token', 'created_at')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used')
    readonly_fields = ('token', 'created_at')
