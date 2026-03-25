from django.urls import path
from .views import (
    RegisterView, CurrentUserView, ProfileView,
    ChangePasswordView, DeleteAccountView, ExportDataView,
    TOTPSetupView, TOTPEnableView, TOTPDisableView, TOTPVerifyView,
    UpdatePreferencesView, UpdateNotificationSettingsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api_register'),
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
]
