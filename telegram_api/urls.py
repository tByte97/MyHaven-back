from django.urls import path

from .views import (
    TelegramBudgetDetailAPI,
    TelegramBudgetListAPI,
    TelegramCalendarAPI,
    TelegramCalendarDayAPI,
    TelegramCategoryListAPI,
    TelegramDashboardAPI,
    TelegramHealthAPI,
    TelegramStatisticsAPI,
    TelegramTransactionDetailAPI,
    TelegramTransactionListAPI,
    TelegramUploadStatementAPI,
)

urlpatterns = [
    path('health/', TelegramHealthAPI.as_view(), name='telegram_health'),
    path('dashboard/', TelegramDashboardAPI.as_view(), name='telegram_dashboard'),
    path('statistics/', TelegramStatisticsAPI.as_view(), name='telegram_statistics'),
    path('categories/', TelegramCategoryListAPI.as_view(), name='telegram_categories'),
    path('calendar/', TelegramCalendarAPI.as_view(), name='telegram_calendar'),
    path('calendar/<int:year>/<int:month>/<int:day>/', TelegramCalendarDayAPI.as_view(), name='telegram_calendar_day'),
    path('transactions/', TelegramTransactionListAPI.as_view(), name='telegram_transactions'),
    path('transactions/<int:pk>/', TelegramTransactionDetailAPI.as_view(), name='telegram_transaction_detail'),
    path('uploads/', TelegramUploadStatementAPI.as_view(), name='telegram_uploads'),
    path('budgets/', TelegramBudgetListAPI.as_view(), name='telegram_budgets'),
    path('budgets/<int:pk>/', TelegramBudgetDetailAPI.as_view(), name='telegram_budget_detail'),
]
