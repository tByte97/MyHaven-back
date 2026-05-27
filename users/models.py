from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    LANGUAGE_CHOICES = [
        ('uk', 'Українська'),
        ('en', 'English'),
        ('de', 'Deutsch'),
        ('es', 'Español'),
        ('pl', 'Polski'),
    ]
    THEME_CHOICES = [
        ('light', 'Frost'),
        ('dark', 'Abyss'),
        ('auto', 'System'),
    ]
    CURRENCY_CHOICES = [
        ('UAH', 'UAH'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('PLN', 'PLN'),
        ('GBP', 'GBP'),
        ('CHF', 'CHF'),
    ]

    email = models.EmailField(unique=True, verbose_name="Електронна пошта")

    # TOTP 2FA
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    totp_enabled = models.BooleanField(default=False)

    # Preferences
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light'
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='uk'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='UAH'
    )
    display_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='UAH',
    )
    tracking_sources = models.JSONField(default=list, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    # Notifications
    email_notifications = models.BooleanField(default=True)
    telegram_notifications = models.BooleanField(default=False)
    notify_large_expense = models.BooleanField(default=True)
    notify_budget_exceeded = models.BooleanField(default=True)
    notify_daily_summary = models.BooleanField(default=False)

    # Telegram Integration
    telegram_user_id = models.BigIntegerField(blank=True, null=True, unique=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class TelegramLinkCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_link_codes',
    )
    code_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Telegram Link Code"
        verbose_name_plural = "Telegram Link Codes"

    def __str__(self):
        return f"Telegram link code for {self.user_id}"
    

