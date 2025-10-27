from django.urls import path
from users.views import * 


urlpatterns = [
    path('', home_view, name='userhome'),

    path('register/', register, name= "register"),
    path('login/', login_view, name = "login"),
    path('logout/', logout_view, name='logout'),
]
