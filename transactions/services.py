"""
Service Layer — вся бізнес-логіка обробки транзакцій.
Views делегують сюди, а не містять логіку самостійно (Service Layer Pattern).
"""
import logging
import os
from typing import List, Dict, Tuple

from django.db import transaction as db_transaction

from .models import Transaction, TransactionUpload
from .parsers import get_parser_for_bank
from .categorization import CategoryMatcher
from accounts.models import Account, Bank

logger = logging.getLogger(__name__)


# ─── Account helpers ────────────────────────────────────────────

def get_or_create_account(user, bank: Bank) -> Account:
    """Повертає існуючий або створює новий рахунок для пари (user, bank)."""
    bank_name = bank.name if bank else 'Основний рахунок'

    account, created = Account.objects.get_or_create(
        user=user,
        bank=bank,
        defaults={
            'account_name': bank_name,
            'account_type': 'BANK',
        },
    )
    if created:
        logger.info("Створено рахунок '%s' для %s", bank_name, user)
    return account


# ─── Transaction creation ──────────────────────────────────────

def _create_transactions(
    account: Account,
    upload: TransactionUpload,
    parsed_data: List[Dict],
) -> Tuple[int, int]:
    """
    Створює транзакції з розпарсених даних. Уникає дублікатів через get_or_create.
    Повертає (created_count, skipped_count).
    """
    matcher = CategoryMatcher(account.user)
    created_count = 0
    skipped_count = 0

    for row in parsed_data:
        category, confidence = matcher.match(
            row['description'],
            row.get('bank_category', ''),
            float(row['amount']),
        )

        _, created = Transaction.objects.get_or_create(
            account=account,
            transaction_date=row['date'],
            amount=row['amount'],
            description=row['description'],
            defaults={
                'category': category,
                'raw_description': row.get('description', ''),
                'bank_category': row.get('bank_category', ''),
                'matched_automatically': category is not None,
                'confidence_score': confidence,
                'source_upload': upload,
            },
        )

        if created:
            created_count += 1
        else:
            skipped_count += 1

    logger.info(
        "Імпорт для рахунку %s: створено %d, пропущено %d",
        account.id, created_count, skipped_count,
    )
    return created_count, skipped_count


# ─── Upload processing (єдина точка входу) ─────────────────────

def process_upload(upload: TransactionUpload) -> None:
    """
    Повний цикл обробки завантаженого файлу:
    1. Визначити парсер по банку
    2. Розпарсити файл
    3. Створити рахунок (якщо потрібно)
    4. Зберегти транзакції
    """
    upload.status = 'PROCESSING'
    upload.save(update_fields=['status'])

    try:
        parser = get_parser_for_bank(upload.bank.name if upload.bank else None)

        file_path = upload.file.path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не знайдено: {file_path}")

        parsed_data = parser.parse(file_path)
        if not parsed_data:
            raise ValueError("Парсер не повернув даних. Перевірте формат файлу.")

        upload.total_transactions = len(parsed_data)
        upload.save(update_fields=['total_transactions'])

        account = get_or_create_account(upload.user, upload.bank)
        created_count, skipped_count = _create_transactions(account, upload, parsed_data)

        upload.status = 'COMPLETED'
        upload.processed_transactions = created_count
        upload.processing_log = (
            f'Успішно оброблено. Створено: {created_count}. '
            f'Пропущено (дублікати): {skipped_count}.'
        )
        upload.save()

    except Exception as e:
        logger.exception("Помилка обробки завантаження #%s", upload.id)
        upload.status = 'FAILED'
        upload.processing_log = str(e)
        upload.save()
        raise
