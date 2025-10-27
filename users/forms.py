# users/forms.py

from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser

class RegisterForm(UserCreationForm):
    
    email = forms.EmailField(label="Адреса електронної пошти", required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Вказуємо, які поля форма має обробляти
        fields = ('username', 'email')
        