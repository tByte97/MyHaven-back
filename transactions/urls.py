from django.urls import path
from . import views
from .views import DashboardStatsAPI, StatisticsAPI, UpdateFilterAPI

app_name = 'transactions'


urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'), 
    
    # path('upload/', views.upload_statement_view, name='upload'), 
    
    path('list/', views.transactions_list_view, name='list'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('categories/', views.categories_view, name='categories'),
    path('files/', views.file_manager_view, name='file_manager'),
    path('files/<int:upload_id>/delete/', views.delete_upload_view, name='delete_upload'),


    path('<int:pk>/', views.transaction_detail_view, name='detail'),

    # api

    path('api/dashboard/', DashboardStatsAPI.as_view(),name='api-dashboard'),
    path('api/statistics/', StatisticsAPI.as_view(),name='api-statistics'),
    path('api/filter/update/', UpdateFilterAPI.as_view(), name='api_update_filter'),

]

