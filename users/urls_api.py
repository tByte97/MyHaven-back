from django.urls import path
from .views import (
    ChangePasswordView,
    CurrentUserView,
    DeleteAccountView,
    ExportDataView,
    LoginTOTPVerifyView,
    LoginView,
    ProfileView,
    RegisterView,
    TelegramRegisterView,
    TOTPDisableView,
    TOTPEnableView,
    TOTPSetupView,
    TOTPVerifyView,
    TelegramLinkCodeCreateView,
    TelegramLinkExchangeView,
    TelegramUnlinkView,
    UpdateNotificationSettingsView,
    UpdatePreferencesView,
)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='api_login'),
    path('auth/verify-totp/', LoginTOTPVerifyView.as_view(), name='api_login_totp_verify'),
    path('register/', RegisterView.as_view(), name='api_register'),
    path('telegram/register/', TelegramRegisterView.as_view(), name='api_telegram_register'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('profile/', ProfileView.as_view(), name='api_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='api_delete_account'),
    path('export-data/', ExportDataView.as_view(), name='api_export_data'),

    # TOTP 2FA
    path('totp/setup/', TOTPSetupView.as_view(), name='api_totp_setup'),
    path('totp/enable/', TOTPEnableView.as_view(), name='api_totp_enable'),
    path('totp/disable/', TOTPDisableView.as_view(), name='api_totp_disable'),
    path('totp/verify/', TOTPVerifyView.as_view(), name='api_totp_verify'),

    # Preferences & Notifications
    path('preferences/', UpdatePreferencesView.as_view(), name='api_update_preferences'),
    path('notifications/', UpdateNotificationSettingsView.as_view(), name='api_update_notifications'),

    # Telegram linking
    path('telegram/link-code/', TelegramLinkCodeCreateView.as_view(), name='api_telegram_link_code'),
    path('telegram/link/', TelegramLinkExchangeView.as_view(), name='api_telegram_link_exchange'),
    path('telegram/unlink/', TelegramUnlinkView.as_view(), name='api_telegram_unlink'),
]
