import base64
import logging
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings as conf_settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import RegisterForm
from .serializers import (
    ChangePasswordSerializer,
    NotificationSettingsSerializer,
    PreferencesSerializer,
    PrivateProfileSerializer,
    TOTPDisableSerializer,
    TOTPEnableSerializer,
    TOTPSetupSerializer,
    TOTPVerifySerializer,
    UserRegSerializer,
)
from .services import AccountDeletionService, ExportService, TelegramLinkService

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


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PrivateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


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
        try:
            AccountDeletionService.delete_user_account(request.user)
        except Exception as exc:
            logger.exception("Failed to delete account for user %s", request.user.id)
            return Response(
                {'error': 'Не вдалося видалити акаунт.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'detail': 'Акаунт видалено.'}, status=status.HTTP_200_OK)


class ExportDataView(APIView):
    # Експорт всіх даних користувача у JSON
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = ExportService.export_all_data(request.user)
        return Response(data)


class TelegramLinkCodeCreateView(APIView):
    """Generate a one-time secret code for Telegram linking."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        secret, expires_at = TelegramLinkService.generate_link_code(request.user)
        return Response({
            'secret': secret,
            'expires_at': expires_at.isoformat(),
        })


class TelegramLinkExchangeView(APIView):
    """Exchange a secret code for JWT tokens and bind Telegram account."""

    permission_classes = [AllowAny]

    def post(self, request):
        secret = request.data.get('secret')
        telegram_user_id = request.data.get('telegram_user_id')
        telegram_username = request.data.get('telegram_username')

        if not secret or telegram_user_id is None:
            return Response(
                {'detail': 'secret and telegram_user_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            telegram_user_id = int(telegram_user_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'telegram_user_id must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = TelegramLinkService.exchange_link_code(
                secret,
                telegram_user_id,
                telegram_username,
            )
        except ValueError as exc:
            if str(exc) == 'telegram_id_taken':
                return Response(
                    {'detail': 'telegram_user_id is already linked.'},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(
                {'detail': 'secret is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

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
        serializer = PreferencesSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated preferences", request.user.id)
        return Response(serializer.data)


class UpdateNotificationSettingsView(APIView):
    # Оновлення налаштувань повідомлень
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = NotificationSettingsSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated notification settings", request.user.id)
        return Response(serializer.data)
