from django.urls import path
from . import views
from .views import DashboardStatsAPI

app_name = 'transactions'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'), 
    
    # path('upload/', views.upload_statement_view, name='upload'), 
    
    path('list/', views.transactions_list_view, name='list'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('categories/', views.categories_view, name='categories'),

    path('<int:pk>/', views.transaction_detail_view, name='detail'),

    # api

    path('api/dashboard/', DashboardStatsAPI.as_view(),name='api-dashboard')
]

