"""
Парсери банківських виписок.
Кожен банк — окремий клас, що наслідує BankStatementParser (Strategy Pattern).
Фабрична функція get_parser_for_bank() повертає потрібний парсер.
"""
import logging
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

import pandas as pd
import pdfplumber
from django.utils import timezone

logger = logging.getLogger(__name__)

# ─── Загальні формати дат (DRY) ────────────────────────────────

COMMON_DATE_FORMATS = [
    '%d.%m.%Y %H:%M:%S',
    '%d.%m.%Y',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%m/%d/%Y',
]


# ─── Базовий клас ──────────────────────────────────────────────

class BankStatementParser:
    """Базовий клас для всіх парсерів банківських виписок."""

    def parse(self, file_path: str) -> List[Dict]:
        raise NotImplementedError

    @staticmethod
    def clean_amount(amount_str) -> Decimal:
        if isinstance(amount_str, (int, float)):
            return Decimal(str(amount_str))
        cleaned = re.sub(r'[^\d\-.,]', '', str(amount_str))
        cleaned = cleaned.replace(',', '.')
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal('0')

    @staticmethod
    def parse_date(date_str: str, formats=None) -> datetime:
        """Парсинг дати з fallback на timezone.now()."""
        formats = formats or COMMON_DATE_FORMATS
        for fmt in formats:
            try:
                naive_dt = datetime.strptime(str(date_str).strip(), fmt)
                return timezone.make_aware(naive_dt)
            except (ValueError, TypeError):
                continue
        logger.warning("Не вдалося розпарсити дату: '%s'", date_str)
        return timezone.now()


# ─── ПриватБанк (Excel) ────────────────────────────────────────

class PrivatBankExcelParser(BankStatementParser):
    def parse(self, file_path: str) -> List[Dict]:
        try:
            df = pd.read_excel(file_path, header=1)
        except Exception as e:
            raise ValueError(f"Не вдалося прочитати Excel: {e}")

        transactions = []
        for _, row in df.iterrows():
            try:
                date_str = str(row.get('Дата', ''))
                amount = self.clean_amount(row.get('Сума в валюті картки', 0))
                if not date_str or amount == 0:
                    continue

                transactions.append({
                    'date': self.parse_date(date_str),
                    'amount': amount,
                    'description': str(row.get('Опис операції', 'Без опису')),
                    'bank_category': str(row.get('Категорія', '')),
                })
            except Exception as e:
                logger.debug("Помилка парсингу рядка PrivatBank: %s", e)
                continue
        return transactions


# ─── Monobank (Excel) ──────────────────────────────────────────

class MonobankExcelParser(BankStatementParser):
    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path)
        transactions = []
        for _, row in df.iterrows():
            try:
                date_str = str(row.get('Дата і час операції', ''))
                amount = self.clean_amount(row.get('Сума', 0))
                if amount == 0:
                    debit = self.clean_amount(row.get('Дебет', 0))
                    credit = self.clean_amount(row.get('Кредит', 0))
                    amount = credit - debit

                transactions.append({
                    'date': self.parse_date(date_str),
                    'amount': amount,
                    'description': str(row.get('Опис операції', row.get('Опис', 'Без опису'))),
                    'bank_category': str(row.get('Категорія', '')),
                })
            except Exception as e:
                logger.debug("Помилка парсингу рядка Monobank: %s", e)
                continue
        return transactions


# ПУМБ (PDF)

class PumbPdfParser(BankStatementParser):
    EXPENSE_KEYWORDS = ('покупка', 'комісія', 'списання', 'переказ')
    def parse(self, file_path: str) -> List[Dict]:
        
        transactions = []
        headers = None 
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                if headers is None:
                    headers = table[0]
                    page_data = table[1:]
                else:
                    page_data = table


                df = pd.DataFrame(page_data, columns=headers)
                df.columns = [col.replace('\n', ' ') if isinstance(col,str) else '' for col in df.columns]

                for _, row in df.iterrows():
                    raw_date = row.get('Дата та час операції')
                    if not raw_date or str(raw_date).strip() == '':
                        continue

                    raw_amount = row.get('Сума операції', '0') or '0'
                    desc_main = str(row.get('Опис операції', '')).replace('\n', ' ')
                    desc_details = str(row.get('Деталі операції', '')).replace('\n', ' ')
                    description = f"{desc_main}: {desc_details}".strip()

                    transactions.append({
                        'date': self._parse_pumb_date(raw_date),
                        'description': description,
                        'amount': self._clean_pumb_amount(str(raw_amount), desc_main),
                        'bank_category': '',
                    })
        return transactions

    def _clean_pumb_amount(self, amount_str: str, operation_type: str) -> Decimal:
        cleaned = amount_str.replace('UAH', '').replace(' ', '').replace('\n', '').replace(',', '.')
        try:
            value = Decimal(cleaned)
        except Exception:
            return Decimal('0')

        if any(kw in operation_type.lower() for kw in self.EXPENSE_KEYWORDS):
            return -abs(value)
        return value

    @staticmethod
    def _parse_pumb_date(date_str) -> datetime:
        clean_date = str(date_str).replace('\n', ' ').strip()
        dt = pd.to_datetime(clean_date).to_pydatetime()
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


# ─── Універсальний CSV ─────────────────────────────────────────

class UniversalCSVParser(BankStatementParser):
    COLUMN_MAP = {
        'date': ['дата', 'date', 'час', 'time'],
        'amount': ['сума', 'amount', 'sum'],
        'description': ['опис', 'description', 'призначення'],
        'category': ['категорія', 'category'],
    }

    def parse(self, file_path: str) -> List[Dict]:
        df = self._read_csv(file_path)
        if df is None:
            return []

        col_map = {key: self._find_column(df.columns, keywords)
                    for key, keywords in self.COLUMN_MAP.items()}

        if not col_map['date'] or not col_map['amount']:
            logger.warning("У CSV не знайдено обов'язкових колонок (дата/сума)")
            return []

        transactions = []
        for _, row in df.iterrows():
            try:
                transactions.append({
                    'date': self.parse_date(str(row[col_map['date']])),
                    'amount': self.clean_amount(row[col_map['amount']]),
                    'description': str(row[col_map['description']]) if col_map['description'] else 'Без опису',
                    'bank_category': str(row[col_map['category']]) if col_map['category'] else '',
                })
            except Exception as e:
                logger.debug("Помилка парсингу рядка CSV: %s", e)
                continue
        return transactions

    @staticmethod
    def _read_csv(file_path: str):
        for sep in [',', ';', '\t']:
            try:
                df = pd.read_csv(file_path, sep=sep)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
        logger.warning("Не вдалося прочитати CSV: %s", file_path)
        return None

    @staticmethod
    def _find_column(columns, keywords):
        for col in columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in keywords):
                return col
        return None


# ─── Фабрика парсерів (єдина точка вибору) ─────────────────────

BANK_PARSERS = {
    'ПриватБанк': PrivatBankExcelParser,
    'Monobank': MonobankExcelParser,
    'ПУМБ': PumbPdfParser,
}


def get_parser_for_bank(bank_name: str = None) -> BankStatementParser:
    """
    Фабричний метод: повертає парсер за назвою банку.
    Якщо банк невідомий — повертає UniversalCSVParser.
    """
    if bank_name and bank_name in BANK_PARSERS:
        return BANK_PARSERS[bank_name]()
    logger.info("Банк '%s' не знайдено в реєстрі, використовую UniversalCSVParser", bank_name)
    return UniversalCSVParser()