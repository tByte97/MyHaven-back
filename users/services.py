import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
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
        return {
            'profile': PrivateProfileSerializer(user).data,
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

        user_model = get_user_model()
        already_linked = user_model.objects.filter(
            telegram_user_id=telegram_user_id,
        ).exclude(id=link.user_id).exists()
        if already_linked:
            raise ValueError("telegram_id_taken")

        user = link.user
        user.telegram_user_id = telegram_user_id
        if telegram_username:
            user.telegram_username = telegram_username
        user.save(update_fields=['telegram_user_id', 'telegram_username'])

        link.used_at = timezone.now()
        link.save(update_fields=['used_at'])

        return user

    @staticmethod
    def _hash_code(code: str) -> str:
        raw = f"{settings.SECRET_KEY}:{code}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _generate_code() -> str:
        return secrets.token_hex(6)
