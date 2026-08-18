import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom user model for AI Live Studio."""

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Verification'),
    ]

    full_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    credits = models.PositiveIntegerField(default=50)
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Set True the moment an admin approves this user's first payment.
    # Stays True permanently after that — even if credits run out later,
    # the user keeps dashboard access (just streaming gets locked, see
    # api/views.py); this flag only controls the *initial* payment gate
    # shown right after registering.
    has_active_access = models.BooleanField(default=False)

    # Referral program: each user gets a unique code; referred_by is set
    # once at registration (from a ?ref= link) and never changes. The
    # referrer earns bonus credits the moment the referred user's FIRST
    # payment is approved (see admin_dashboard/views.py approve_payment_view).
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    is_email_verified = models.BooleanField(default=False)

    # Private token powering this user's OBS Browser Source URL (like a
    # stream key). This has nothing to do with connecting an external AI
    # API — it's purely a capability token so OBS can privately fetch this
    # user's AI program output as a Browser Source.
    obs_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    bio = models.TextField(blank=True, max_length=500)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def generate_obs_token(self):
        self.obs_token = secrets.token_urlsafe(32)
        self.save(update_fields=['obs_token'])
        return self.obs_token

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = secrets.token_hex(4)  # 8-char code, e.g. "a1b2c3d4"
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = list(kwargs['update_fields']) + ['referral_code']
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.full_name or self.username

    def has_enough_credits(self, amount):
        return self.credits >= amount

    def deduct_credits(self, amount):
        if self.has_enough_credits(amount):
            self.credits -= amount
            self.save(update_fields=['credits'])
            return True
        return False

    def add_credits(self, amount):
        self.credits += amount
        self.save(update_fields=['credits'])


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and (timezone.now() - self.created_at).total_seconds() < 86400

    def __str__(self):
        return f'Verification token for {self.user.username}'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and (timezone.now() - self.created_at).total_seconds() < 3600

    def __str__(self):
        return f'Password reset token for {self.user.username}'
