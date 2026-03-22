from django.urls import path
from .views import (
    RegisterView, CurrentUserView, ProfileView,
    ChangePasswordView, DeleteAccountView, ExportDataView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api_register'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('profile/', ProfileView.as_view(), name='api_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='api_delete_account'),
    path('export-data/', ExportDataView.as_view(), name='api_export_data'),
]
