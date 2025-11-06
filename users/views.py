# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm 
from core.settings import LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL

@login_required
def home_view(request): 
    context = {
        'user': request.user
    }
    return render(request, 'userhome.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(LOGIN_REDIRECT_URL)
        else:
            print("!!!!!!!!")
            print(form.errors)
    else:
        # Це GET-запит
        form = RegisterForm() 
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = AuthenticationForm(request, data = request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username = username, password = password)
            if user is not None:
                login(request, user)
                return redirect(LOGIN_REDIRECT_URL)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form}) 

def logout_view(request):
    logout(request)
    return redirect(LOGOUT_REDIRECT_URL)