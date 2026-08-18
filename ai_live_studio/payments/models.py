import uuid

from django.conf import settings
from django.db import models


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    METHOD_CHOICES = [
        ('card', 'Credit / Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('credits_purchase', 'Credits Purchase'),
        ('subscription', 'Subscription'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    reference = models.CharField(max_length=40, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='card')
    description = models.CharField(max_length=255, blank=True)
    credits_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reference} - {self.user.username} - ${self.amount}'


class CreditPackage(models.Model):
    """Purchasable credit bundles shown on the Credits page."""

    name = models.CharField(max_length=50)
    credits = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_popular = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.name} - {self.credits} credits (${self.price})'


class CreditPlan(models.Model):
    """
    The single source of truth for pricing plans, fully controlled by the
    admin dashboard. Replaces the old hardcoded pricing on the landing
    page and billing screen — created/edited/deleted here, and changes
    show up immediately on the public payment page.
    """

    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.PositiveIntegerField()
    minutes_label = models.CharField(
        max_length=40, blank=True,
        help_text='Free-text, e.g. "6 mins" — shown to users as a rough usage estimate.'
    )
    description = models.TextField(
        blank=True, help_text='Shown to users on the payment page, e.g. feature bullet points.'
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'price']

    def __str__(self):
        return f'{self.name} — ${self.price} ({self.credits} credits)'


class PaymentMethod(models.Model):
    """
    A payment option the admin has set up (bank account or crypto wallet)
    that users see and pay into on the payment page. Fully admin-managed —
    up to 3 bank accounts and 4 crypto wallets is a UI guideline, not a
    hard limit enforced here.
    """

    METHOD_TYPE_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
    ]

    method_type = models.CharField(max_length=10, choices=METHOD_TYPE_CHOICES)

    # Bank transfer fields
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=60, blank=True)
    routing_or_swift = models.CharField(max_length=60, blank=True, help_text='Routing number, SWIFT/BIC, or IBAN.')

    # Crypto fields
    crypto_currency = models.CharField(
        max_length=20, blank=True,
        help_text='e.g. BTC, USDT, ETH, SOL'
    )
    wallet_address = models.CharField(max_length=255, blank=True)
    network_note = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. "USDT — TRC20 network only"'
    )

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'method_type']

    def __str__(self):
        if self.method_type == 'bank':
            return f'{self.bank_name} — {self.account_number}'
        return f'{self.crypto_currency} — {self.wallet_address[:16]}…'


def receipt_upload_path(instance, filename):
    import uuid
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'receipts/{instance.user_id}/{uuid.uuid4().hex}.{ext}'


class PaymentSubmission(models.Model):
    """
    A user's claim of having paid for a plan — bank transfer or crypto,
    with an uploaded receipt/proof screenshot. Sits in 'pending' until an
    admin reviews it in /admin_dashboard/ and approves or rejects it.
    Approving is what actually grants the user their credits and (for a
    first-time approval) unlocks dashboard access.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_submissions')
    plan = models.ForeignKey(CreditPlan, on_delete=models.SET_NULL, null=True, related_name='submissions')
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='submissions')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.ImageField(upload_to=receipt_upload_path)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_note = models.CharField(max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.plan} — {self.get_status_display()}'


class PlatformSetting(models.Model):
    """
    Singleton row for platform-wide settings the admin can change from the
    dashboard without a redeploy.
    """

    decart_api_key_override = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Leave blank to use the DECART_API_KEY environment variable instead.'
    )
    support_telegram_username = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Telegram username only, e.g. supportcreoveya or @supportcreoveya.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform Setting'
        verbose_name_plural = 'Platform Settings'

    def __str__(self):
        return 'Platform Settings'

    @property
    def telegram_support_url(self):
        username = (self.support_telegram_username or '').strip()
        if not username:
            return 'https://t.me/'
        cleaned = username.lstrip('@')
        return f'https://t.me/{cleaned}'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
