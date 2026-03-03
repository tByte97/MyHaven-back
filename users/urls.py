from django.urls import path
from .views import home_view, register, login_view, logout_view

urlpatterns = [
    path('', home_view, name='userhome'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
