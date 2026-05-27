import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction as db_transaction
from django.utils import timezone

from budgets.models import Budget
from transactions.models import Transaction, TransactionUpload
from transactions.serializers import TransactionSerializer

from .serializers import (
    NotificationSettingsSerializer,
    PreferencesSerializer,
    PrivateProfileSerializer,
)
from .models import TelegramLinkCode

logger = logging.getLogger(__name__)


class ExportService:
    """Сервіс експорту даних користувача."""

    @staticmethod
    def export_all_data(user) -> Dict:
        profile = PrivateProfileSerializer(user).data
        profile.pop('telegram_user_id', None)
        profile.pop('telegram_username', None)
        return {
            'profile': profile,
            'preferences': PreferencesSerializer(user).data,
            'notifications': NotificationSettingsSerializer(user).data,
            'transactions': ExportService._export_transactions(user),
            'budgets': ExportService._export_budgets(user),
            'uploads': ExportService._export_uploads(user),
        }

    @staticmethod
    def _export_transactions(user) -> List[Dict]:
        transactions = Transaction.objects.filter(
            account__user=user,
        ).select_related('category', 'account')
        return TransactionSerializer(transactions, many=True).data

    @staticmethod
    def _export_budgets(user) -> List[Dict]:
        budgets = Budget.objects.filter(user=user).select_related('category')
        return [
            {
                'category': b.category.name,
                'month': str(b.month),
                'amount': str(b.amount),
            }
            for b in budgets
        ]

    @staticmethod
    def _export_uploads(user) -> List[Dict]:
        uploads = TransactionUpload.objects.filter(user=user).select_related('bank')
        return [
            {
                'id': u.id,
                'bank': str(u.bank) if u.bank else None,
                'status': u.status,
                'uploaded_at': u.uploaded_at.isoformat(),
                'total_transactions': u.total_transactions,
                'processed_transactions': u.processed_transactions,
            }
            for u in uploads
        ]


class AccountDeletionService:
    """Сервіс безпечного видалення акаунта користувача."""

    @staticmethod
    def delete_user_account(user) -> None:
        user_id = user.id
        with db_transaction.atomic():
            Transaction.objects.filter(account__user=user).delete()
            TransactionUpload.objects.filter(user=user).delete()
            Budget.objects.filter(user=user).delete()
            user.delete()
        logger.info("User %s account deleted successfully", user_id)


class SecurityNotificationService:
    """Email notifications for sensitive account events."""

    @staticmethod
    def send_password_changed(user) -> None:
        SecurityNotificationService._send(
            subject='MyHaven: password changed',
            message=(
                f'Hello, {user.username}!\n\n'
                'Your MyHaven account password was changed successfully.\n'
                'If this was not you, change the password immediately and contact support.'
            ),
            recipients=[user.email],
        )

    @staticmethod
    def send_email_changed(user, old_email: str, new_email: str) -> None:
        old_message = (
            f'Hello, {user.username}!\n\n'
            f'The email for your MyHaven account was changed from {old_email} to {new_email}.\n'
            'If you did not request this change, secure your account immediately.'
        )
        new_message = (
            f'Hello, {user.username}!\n\n'
            f'This address ({new_email}) was added as the new email for your MyHaven account.\n'
            'If this change was unexpected, please contact support.'
        )

        SecurityNotificationService._send(
            subject='MyHaven: email changed',
            message=old_message,
            recipients=[old_email],
        )
        if new_email != old_email:
            SecurityNotificationService._send(
                subject='MyHaven: new email confirmed',
                message=new_message,
                recipients=[new_email],
            )

    @staticmethod
    def _send(subject: str, message: str, recipients: List[str]) -> None:
        if not recipients:
            return
        if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
            logger.warning('Security email skipped: email backend is not configured.')
            return

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception:
            logger.exception('Failed to send security email to %s', recipients)


class TOTPLoginService:
    """Utility helpers for two-step JWT login flow."""

    TOKEN_SALT = 'users.totp.login'
    TOKEN_MAX_AGE_SECONDS = 300

    @staticmethod
    def create_login_token(user) -> str:
        return signing.dumps({'user_id': user.id}, salt=TOTPLoginService.TOKEN_SALT)

    @staticmethod
    def resolve_login_token(token: str):
        payload = signing.loads(
            token,
            salt=TOTPLoginService.TOKEN_SALT,
            max_age=TOTPLoginService.TOKEN_MAX_AGE_SECONDS,
        )
        return get_user_model().objects.get(id=payload['user_id'])


class TelegramLinkService:
    """Service for generating and exchanging Telegram link codes."""

    DEFAULT_TTL_MINUTES = 10

    @staticmethod
    def generate_link_code(user, ttl_minutes: int = DEFAULT_TTL_MINUTES) -> Tuple[str, timezone.datetime]:
        TelegramLinkCode.objects.filter(
            user=user,
            used_at__isnull=True,
        ).update(used_at=timezone.now())

        code = TelegramLinkService._generate_code()
        code_hash = TelegramLinkService._hash_code(code)
        expires_at = timezone.now() + timedelta(minutes=ttl_minutes)

        TelegramLinkCode.objects.create(
            user=user,
            code_hash=code_hash,
            expires_at=expires_at,
        )

        return code, expires_at

    @staticmethod
    def exchange_link_code(
        secret: str,
        telegram_user_id: int,
        telegram_username: Optional[str] = None,
    ):
        code_hash = TelegramLinkService._hash_code(secret)
        link = TelegramLinkCode.objects.select_related('user').filter(
            code_hash=code_hash,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()

        if not link:
            raise ValueError("invalid_or_expired")

        user = link.user
        TelegramLinkService.link_user(
            user,
            telegram_user_id,
            telegram_username,
        )

        link.used_at = timezone.now()
        link.save(update_fields=['used_at'])

        return user

    @staticmethod
    def link_user(
        user,
        telegram_user_id: int,
        telegram_username: Optional[str] = None,
    ) -> None:
        user_model = get_user_model()
        already_linked = user_model.objects.filter(
            telegram_user_id=telegram_user_id,
        ).exclude(id=user.id).exists()
        if already_linked:
            raise ValueError("telegram_id_taken")

        user.telegram_user_id = telegram_user_id
        user.telegram_username = telegram_username or None
        user.save(update_fields=['telegram_user_id', 'telegram_username'])

    @staticmethod
    def unlink_user(user) -> None:
        TelegramLinkCode.objects.filter(
            user=user,
            used_at__isnull=True,
        ).update(used_at=timezone.now())

        user.telegram_user_id = None
        user.telegram_username = None
        user.telegram_notifications = False
        user.save(update_fields=[
            'telegram_user_id',
            'telegram_username',
            'telegram_notifications',
        ])

    @staticmethod
    def _hash_code(code: str) -> str:
        raw = f"{settings.SECRET_KEY}:{code}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _generate_code() -> str:
        return secrets.token_hex(6)
