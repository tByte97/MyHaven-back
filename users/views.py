import base64
import logging
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings as conf_settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core import signing
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import RegisterForm
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    NotificationSettingsSerializer,
    PreferencesSerializer,
    PrivateProfileSerializer,
    TelegramRegisterSerializer,
    TOTPDisableSerializer,
    TOTPEnableSerializer,
    TOTPLoginChallengeSerializer,
    TOTPSetupSerializer,
    TOTPVerifySerializer,
    UserRegSerializer,
)
from .services import (
    AccountDeletionService,
    ExportService,
    SecurityNotificationService,
    TelegramLinkService,
    TOTPLoginService,
)

logger = logging.getLogger(__name__)


def _build_token_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'requires_totp': False,
    }


# Template Views
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


# REST API Views
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegSerializer
    permission_classes = [AllowAny]


class TelegramRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TelegramRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_user_id = serializer.validated_data['telegram_user_id']
        telegram_username = serializer.validated_data.get('telegram_username')

        try:
            with db_transaction.atomic():
                user = serializer.save()
                TelegramLinkService.link_user(
                    user,
                    telegram_user_id,
                    telegram_username,
                )
        except ValueError as exc:
            if str(exc) == 'telegram_id_taken':
                return Response(
                    {'detail': 'telegram_user_id is already linked.'},
                    status=status.HTTP_409_CONFLICT,
                )
            raise

        return Response(
            _build_token_response(user),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Невірний логін або пароль.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.totp_enabled and user.totp_secret:
            return Response({
                'requires_totp': True,
                'login_token': TOTPLoginService.create_login_token(user),
            })

        return Response(_build_token_response(user))


class LoginTOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TOTPLoginChallengeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = TOTPLoginService.resolve_login_token(serializer.validated_data['login_token'])
        except (signing.BadSignature, signing.SignatureExpired):
            return Response(
                {'detail': 'Сесія входу застаріла. Увійдіть знову.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.exception('Failed to resolve TOTP login token.')
            return Response(
                {'detail': 'Не вдалося завершити вхід.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        totp = pyotp.TOTP(user.totp_secret or '')
        if not user.totp_enabled or not user.totp_secret or not totp.verify(
            serializer.validated_data['code'],
            valid_window=1,
        ):
            return Response(
                {'detail': 'Невірний TOTP код.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(_build_token_response(user))


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(PrivateProfileSerializer(request.user).data)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PrivateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        old_email = request.user.email
        response = super().partial_update(request, *args, **kwargs)
        new_email = response.data.get('email', old_email)
        if new_email != old_email:
            SecurityNotificationService.send_email_changed(request.user, old_email, new_email)
        return response


class ChangePasswordView(APIView):
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
        request.user.save(update_fields=['password'])
        SecurityNotificationService.send_password_changed(request.user)
        logger.info("User %s changed password", request.user.id)
        return Response({'detail': 'Пароль успішно змінено.'})


class DeleteAccountView(APIView):
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
        except Exception:
            logger.exception("Failed to delete account for user %s", request.user.id)
            return Response(
                {'error': 'Не вдалося видалити акаунт.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'detail': 'Акаунт видалено.'}, status=status.HTTP_200_OK)


class ExportDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = ExportService.export_all_data(request.user)
        return Response(data)


class TelegramLinkCodeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        secret, expires_at = TelegramLinkService.generate_link_code(request.user)
        return Response({
            'secret': secret,
            'expires_at': expires_at.isoformat(),
        })


class TelegramUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        TelegramLinkService.unlink_user(request.user)
        logger.info("User %s unlinked Telegram profile", request.user.id)
        return Response({'detail': 'Telegram account unlinked.'})


class TelegramLinkExchangeView(APIView):
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

        return Response(_build_token_response(user))


class TOTPSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name='MyHaven',
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        serializer = TOTPSetupSerializer(data={
            'qr_code': f'data:image/png;base64,{img_str}',
            'secret': secret,
        })
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class TOTPEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TOTPEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        secret = serializer.validated_data['secret']
        code = serializer.validated_data['code']
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            return Response(
                {'error': 'Невірний код. Спробуйте ще раз.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.totp_secret = secret
        request.user.totp_enabled = True
        request.user.save(update_fields=['totp_secret', 'totp_enabled'])

        logger.info("User %s enabled TOTP 2FA", request.user.id)
        return Response({'detail': 'TOTP успішно увімкнено.'})


class TOTPDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TOTPDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        if not request.user.check_password(password):
            return Response(
                {'error': 'Невірний пароль.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.totp_secret = None
        request.user.totp_enabled = False
        request.user.save(update_fields=['totp_secret', 'totp_enabled'])

        logger.info("User %s disabled TOTP 2FA", request.user.id)
        return Response({'detail': 'TOTP вимкнено.'})


class TOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.totp_enabled or not request.user.totp_secret:
            return Response(
                {'error': 'TOTP не увімкнено для цього користувача.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = serializer.validated_data['code']
        totp = pyotp.TOTP(request.user.totp_secret)
        if totp.verify(code, valid_window=1):
            return Response({'detail': 'Код підтверджено.', 'verified': True})

        return Response(
            {'error': 'Невірний код.', 'verified': False},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UpdatePreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = PreferencesSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated preferences", request.user.id)
        return Response(serializer.data)


class UpdateNotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = NotificationSettingsSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User %s updated notification settings", request.user.id)
        return Response(serializer.data)
