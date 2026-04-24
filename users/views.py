import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings as conf_settings

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .forms import RegisterForm
from .serializers import UserRegSerializer, ProfileSerializer, ChangePasswordSerializer

logger = logging.getLogger(__name__)


#Template Views

@login_required
def home_view(request):
    return render(request, 'userhome.html', {'user': request.user})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(conf_settings.LOGIN_REDIRECT_URL)
        else:
            logger.warning("Registration form errors: %s", form.errors)
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(conf_settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect(conf_settings.LOGIN_REDIRECT_URL)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect(conf_settings.LOGOUT_REDIRECT_URL)


#REST API Views
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegSerializer
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        })


class ProfileView(APIView):
    # Отримати або оновити профіль користувача
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    # Зміна пароля поточного користувача
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Невірний поточний пароль.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        logger.info("User %s changed password", request.user.id)
        return Response({'detail': 'Пароль успішно змінено.'})


class DeleteAccountView(APIView):
    # Видалення акаунта + підтвердження пароля
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            return Response(
                {'password': ['Невірний пароль.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id = request.user.id
        request.user.delete()
        logger.info("User %s deleted their account", user_id)
        return Response({'detail': 'Акаунт видалено.'}, status=status.HTTP_204_NO_CONTENT)


class ExportDataView(APIView):
    # Експорт всіх даних користувача у JSON
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from transactions.models import Transaction, TransactionUpload
        from transactions.serializers import TransactionSerializer
        from budgets.models import Budget

        user = request.user
        transactions = Transaction.objects.filter(
            account__user=user,
        ).select_related('category', 'account')

        budgets = Budget.objects.filter(user=user).select_related('category')

        uploads = TransactionUpload.objects.filter(user=user)

        data = {
            'profile': ProfileSerializer(user).data,
            'transactions': TransactionSerializer(transactions, many=True).data,
            'budgets': [
                {
                    'category': b.category.name,
                    'month': str(b.month),
                    'amount': str(b.amount),
                }
                for b in budgets
            ],
            'uploads': [
                {
                    'id': u.id,
                    'bank': str(u.bank) if u.bank else None,
                    'status': u.status,
                    'uploaded_at': u.uploaded_at.isoformat(),
                    'total_transactions': u.total_transactions,
                }
                for u in uploads
            ],
        }
        return Response(data)

#TOTP 2FA Views
import pyotp
import qrcode
from io import BytesIO
import base64
from .serializers import TOTPSetupSerializer

class TOTPSetupView(APIView):
    # Генерація QR коду для налаштування TOTP
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Generate new secret
        secret = pyotp.random_base32()

        # Create provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name='MyHaven'
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        data = {
            'qr_code': f'data:image/png;base64,{img_str}',
            'secret': secret
        }

        serializer = TOTPSetupSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

from .serializers import TOTPEnableSerializer

class TOTPEnableView(APIView):
    # Активація TOTP після верифікації 
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = TOTPEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        secret = serializer.validated_data['secret']
        code = serializer.validated_data['code']

        # Verify the code
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            return Response(
                {'error': 'Невірний код. Спробуйте ще раз.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save secret and enable TOTP
        request.user.totp_secret = secret
        request.user.totp_enabled = True
        request.user.save()

        logger.info("User %s enabled TOTP 2FA", request.user.id)
        return Response({'detail': 'TOTP успішно увімкнено.'})


class TOTPDisableView(APIView):
    # Вимкнення TOTP (потребує пароль)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .serializers import TOTPDisableSerializer

        serializer = TOTPDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']

        if not request.user.check_password(password):
            return Response(
                {'error': 'Невірний пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.totp_secret = None
        request.user.totp_enabled = False
        request.user.save()

        logger.info("User %s disabled TOTP 2FA", request.user.id)
        return Response({'detail': 'TOTP вимкнено.'})



from .serializers import TOTPVerifySerializer

class TOTPVerifyView(APIView):
    # Верифікація TOTP коду для логіну
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.totp_enabled or not request.user.totp_secret:
            return Response(
                {'error': 'TOTP не увімкнено для цього користувача.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = serializer.validated_data['code']
        totp = pyotp.TOTP(request.user.totp_secret)

        if totp.verify(code, valid_window=1):
            return Response({'detail': 'Код підтверджено.', 'verified': True})
        else:
            return Response(
                {'error': 'Невірний код.', 'verified': False},
                status=status.HTTP_400_BAD_REQUEST
            )


#Preferences & Notifications Views


class UpdatePreferencesView(APIView):
    # Оновлення налаштувань теми, мови, валюти
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        from .serializers import PreferencesSerializer

        serializer = PreferencesSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated preferences", request.user.id)
        return Response(serializer.data)


class UpdateNotificationSettingsView(APIView):
    # Оновлення налаштувань повідомлень
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        from .serializers import NotificationSettingsSerializer

        serializer = NotificationSettingsSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated notification settings", request.user.id)
        return Response(serializer.data)
