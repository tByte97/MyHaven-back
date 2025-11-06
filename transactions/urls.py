from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'), 
    
    # path('upload/', views.upload_statement_view, name='upload'), # <-- ЦЕЙ РЯДОК БІЛЬШЕ НЕ ПОТРІБЕН
    
    path('list/', views.transactions_list_view, name='list'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('categories/', views.categories_view, name='categories'),

    path('<int:pk>/', views.transaction_detail_view, name='detail'),
]

