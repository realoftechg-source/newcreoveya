from django.contrib import admin

from payments.models import CreditPackage, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'amount', 'status', 'method', 'credits_awarded', 'created_at')
    list_filter = ('status', 'method', 'created_at')
    search_fields = ('reference', 'user__username', 'description')
    date_hierarchy = 'created_at'


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits', 'price', 'is_popular', 'active')
    list_editable = ('is_popular', 'active')
