from django.urls import path
from . import views
from .views import (
    DashboardStatsAPI, StatisticsAPI, UpdateFilterAPI,
    TransactionListAPI, TransactionCreateAPI, TransactionDetailAPI,
    CategoryListAPI, CalendarAPI, CalendarDayAPI,
    UploadListAPI, UploadDetailAPI, BankListAPI,
)

app_name = 'transactions'


urlpatterns = [
    # ── Template views ──
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('list/', views.transactions_list_view, name='list'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('categories/', views.categories_view, name='categories'),
    path('files/', views.file_manager_view, name='file_manager'),
    path('files/<int:upload_id>/delete/', views.delete_upload_view, name='delete_upload'),
    path('<int:pk>/', views.transaction_detail_view, name='detail'),

    # ── REST API ──
    path('api/dashboard/', DashboardStatsAPI.as_view(), name='api-dashboard'),
    path('api/statistics/', StatisticsAPI.as_view(), name='api-statistics'),
    path('api/filter/update/', UpdateFilterAPI.as_view(), name='api_update_filter'),

    # Transactions CRUD
    path('api/list/', TransactionListAPI.as_view(), name='api-transactions-list'),
    path('api/create/', TransactionCreateAPI.as_view(), name='api-transaction-create'),
    path('api/<int:pk>/', TransactionDetailAPI.as_view(), name='api-transaction-detail'),

    # Categories
    path('api/categories/', CategoryListAPI.as_view(), name='api-categories'),

    # Calendar
    path('api/calendar/', CalendarAPI.as_view(), name='api-calendar'),
    path('api/calendar/<int:year>/<int:month>/<int:day>/', CalendarDayAPI.as_view(), name='api-calendar-day'),

    # Uploads / File Manager
    path('api/uploads/', UploadListAPI.as_view(), name='api-uploads'),
    path('api/uploads/<int:pk>/', UploadDetailAPI.as_view(), name='api-upload-detail'),

    # Banks
    path('api/banks/', BankListAPI.as_view(), name='api-banks'),
]

