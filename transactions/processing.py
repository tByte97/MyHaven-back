import pandas as pd
from typing import List, Dict
import os
from django.conf import settings
from .models import Transaction, Category, Account, TransactionUpload, Bank
from .parsers import PrivatBankExcelParser, MonobankExcelParser, UniversalCSVParser, PDFStatementParser
from .categorization import find_category_for_transaction

# ств. транзакіця + уникнення дублів
def _create_transactions_from_data(account: Account, parsed_data: List[Dict]):
    created_count = 0
    skipped_count = 0

    for row in parsed_data:
        
        category, confidence = find_category_for_transaction(
            user=account.user,
            description=row['description'],
            bank_category=row['bank_category'],
            amount=row['amount']
        )
        
        obj, created = Transaction.objects.get_or_create(
            account=account,
            transaction_date=row['date'],
            amount=row['amount'],
            description=row['description'],
            defaults={
                'category': category,
                'bank_category': row['bank_category'],        
                'raw_description': row.get('description', ''),
                'matched_automatically': category is not None,
                'confidence_score': confidence                
            }
        )
        
        if created:
            created_count += 1
        else:
            skipped_count += 1
            
    print(f"Import complete for account {account.id}. Created: {created_count}, Skipped (Duplicates): {skipped_count}")
    return created_count, skipped_count

# ств. рахунка для користувача з врахуванням банку
def get_or_create_account(user, bank: Bank) -> Account:

    if not bank:
        bank_name = "Мій рахунок"
    else:
        bank_name = bank.name

    account, created = Account.objects.get_or_create(
        user=user,
        bank=bank,
        defaults={
            'account_name': f'{bank_name} (Основний)',
            'account_type': 'BANK'
        }
    )
    
    return account

# Обробка завантаженого файлу
def process_upload(upload: TransactionUpload):

    upload.status = 'PROCESSING'
    upload.save()
    
    try:
        # 1. Карта парсерів
        BANK_PARSERS = {
            'ПриватБанк': PrivatBankExcelParser,
            'Monobank': MonobankExcelParser,
        }

        bank_name = upload.bank.name if upload.bank else None
        
        if bank_name in BANK_PARSERS:
            parser = BANK_PARSERS[bank_name]()
        else:
            parser = UniversalCSVParser()

        
        file_path = upload.file.path 
        if not os.path.exists(file_path):
             raise FileNotFoundError(f"Файл не знайдено: {file_path}")
            
        transactions_data = parser.parse(file_path)
        
        if not transactions_data:
             raise ValueError("Парсер не повернув даних. Файл порожній або невідомий формат.")

        account = get_or_create_account(upload.user, upload.bank)
        created_count, skipped_count = _create_transactions_from_data(account, transactions_data)
        
        upload.status = 'COMPLETED'
        upload.processing_log = f'Успішно оброблено. Створено: {created_count}. Пропущено (дублікати): {skipped_count}.'
        upload.save()
            
    except Exception as e:
        upload.status = 'FAILED'
        upload.processing_log = str(e)
        upload.save()
        raise 