# transactions/parsers.py

import pandas as pd
import PyPDF2
import pdfplumber
from datetime import datetime
from decimal import Decimal
import re
from typing import List, Dict
from django.utils import timezone   

# Базовий клас для парсерів
class BankStatementParser:
    
    def parse(self, file_path: str) -> List[Dict]:
        raise NotImplementedError
    
    def clean_amount(self, amount_str: str) -> Decimal:
        """Очищення суми від зайвих символів"""
        if isinstance(amount_str, (int, float)):
            return Decimal(str(amount_str))
        
        cleaned = re.sub(r'[^\d\-.,]', '', str(amount_str))
        cleaned = cleaned.replace(',', '.')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')


# Парсер для Excel виписок ПриватБанку
class PrivatBankExcelParser(BankStatementParser):
    
    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path, header=1)
        # print("---СТОВПЦІ У ФАЙЛІ---:", df.columns.to_list())

        transactions = []
        
        for _, row in df.iterrows():
            try:
                date_str = str(row.get('Дата', ''))
                trans_date = self._parse_date(date_str)

                amount = self.clean_amount(row.get('Сума в валюті картки', 0))
                
                description = str(row.get('Опис операції', 'Без опису'))
                
                bank_category = str(row.get('Категорія', ''))
                
                if not date_str or amount == 0:
                    continue

                transactions.append({
                    'date': trans_date,
                    'amount': amount,
                    'description': description,
                    'bank_category': bank_category,
                    'raw_data': row.to_dict()
                })
            except Exception as e:
                print(f"Помилка парсингу рядка: {e}")
                continue
        
        return transactions
    
    def _parse_date(self, date_str: str) -> datetime:
        formats = [
            '%d.%m.%Y',
            '%d.%m.%Y %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                naive_dt = datetime.strptime(date_str.strip(), fmt)
                return timezone.make_aware(naive_dt) 
            except:
                continue
        return timezone.now()


# Парсер для Excel виписок Монобанку
class MonobankExcelParser(BankStatementParser):
    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_excel(file_path)
        transactions = []
        for _, row in df.iterrows():
            try:
                date_str = str(row.get('Дата і час операції', ''))
                trans_date = self._parse_date(date_str)

                amount = self.clean_amount(row.get('Сума', 0))
                if amount == 0:
                    debit = self.clean_amount(row.get('Дебет', 0))
                    credit = self.clean_amount(row.get('Кредит', 0))
                    amount = credit - debit

                description = str(row.get('Опис операції', row.get('Опис', 'Без опису')))
                bank_category = str(row.get('Категорія', ''))

                transactions.append({
                    'date': trans_date,
                    'amount': amount,
                    'description': description,
                    'bank_category': bank_category,
                    'raw_data': row.to_dict()
                })
            except Exception as e:
                print(f"Помилка парсингу рядка: {e}")
                continue
        return transactions

    def _parse_date(self, date_str: str) -> datetime:
        formats = [
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                naive_dt = datetime.strptime(date_str.strip(), fmt)
                return timezone.make_aware(naive_dt) 
            except:
                continue

        return timezone.now()


# Універсальний парсер для CSV файлів
class UniversalCSVParser(BankStatementParser):
    def parse(self, file_path: str) -> List[Dict]:
        for sep in [',', ';', '\t']:
            try:
                df = pd.read_csv(file_path, sep=sep)
                if len(df.columns) > 1:
                    break
            except:
                continue
        
        transactions = []
        
        for _, row in df.iterrows():
            try:
                date_col = self._find_column(df.columns, ['дата', 'date', 'час', 'time'])
                amount_col = self._find_column(df.columns, ['сума', 'amount', 'sum'])
                desc_col = self._find_column(df.columns, ['опис', 'description', 'призначення'])
                category_col = self._find_column(df.columns, ['категорія', 'category'])
                
                if not date_col or not amount_col:
                    continue
                
                trans_date = self._parse_date(str(row[date_col]))
                amount = self.clean_amount(row[amount_col])
                description = str(row[desc_col]) if desc_col else 'Без опису'
                bank_category = str(row[category_col]) if category_col else ''
                
                transactions.append({
                    'date': trans_date,
                    'amount': amount,
                    'description': description,
                    'bank_category': bank_category,
                    'raw_data': row.to_dict()
                })
            except Exception as e:
                print(f"Помилка парсингу рядка: {e}")
                continue
        
        return transactions
    
    # Знаходження стовпця за ключовими словами
    def _find_column(self, columns, keywords):
        for col in columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
            formats = [
                '%d.%m.%Y',
                '%d.%m.%Y %H:%M:%S',
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y',
            ]

            for fmt in formats:
                try:
                    naive_dt = datetime.strptime(date_str.strip(), fmt)
                    return timezone.make_aware(naive_dt) 
                except:
                    continue
            return timezone.now()


    #Базовий парсер для PDF 
class PDFStatementParser(BankStatementParser):
    
    def parse(self, file_path: str) -> List[Dict]:
        transactions = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()

                    pass
        except Exception as e:
            print(f"Помилка читання PDF: {e}")
        
        return transactions


# Визначення парсеру за розширенням та вмістом файлу
def detect_parser(file_path: str) -> BankStatementParser:
    
    if file_path.lower().endswith('.csv'):
        return UniversalCSVParser()
    
    elif file_path.lower().endswith(('.xls', '.xlsx')):

        df = pd.read_excel(file_path, nrows=5)
        columns_str = ' '.join([str(col).lower() for col in df.columns])
        
        if 'приват' in columns_str or 'privatbank' in columns_str:
            return PrivatBankExcelParser()
        elif 'monobank' in columns_str or 'монобанк' in columns_str:
            return MonobankExcelParser()
        else:

            return PrivatBankExcelParser()
    
    elif file_path.lower().endswith('.pdf'):
        return PDFStatementParser()
    
    else:
        raise ValueError(f"Непідтримуваний формат файлу: {file_path}")