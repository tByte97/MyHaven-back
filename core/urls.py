
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Template views (Django sessions)
    path('', include('users.urls')),
    path('transactions/', include('transactions.urls')),

    # REST API
    path('api/users/', include('users.urls_api')),
    path('api/budgets/', include('budgets.urls')),
    path('api/telegram/', include('telegram_api.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh')    ,
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# MEDIA_ROOT містить банківські виписки користувачів, тому навіть у DEBUG
# його не роздаємо статикою: файли віддає transactions:api-upload-file
# з перевіркою власника.
