from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, Bank
from transactions.models import Transaction, TransactionUpload
from transactions.parsers import PumbPdfParser
from transactions.repositories import TransactionRepository
from transactions.services import process_upload


class BackendCLUnitTests(TestCase):
    def _create_user(self, username: str, email: str):
        return get_user_model().objects.create_user(
            username=username,
            email=email,
            password='Pass1234!'
        )

    def test_database_connection(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            row = cursor.fetchone()

        self.assertEqual(row[0], 1)

    def test_successful_statement_upload_processing(self):
        user = self._create_user('uploader', 'uploader@example.com')
        bank = Bank.objects.create(name='Monobank')

        upload = TransactionUpload.objects.create(
            user=user,
            bank=bank,
            file=SimpleUploadedFile('statement.csv', b'dummy,data', content_type='text/csv')
        )

        parsed_data = [
            {
                'date': timezone.now(),
                'amount': Decimal('-120.50'),
                'description': 'Покупка в АТБ',
                'bank_category': 'Супермаркет',
            },
            {
                'date': timezone.now(),
                'amount': Decimal('300.00'),
                'description': 'Повернення коштів',
                'bank_category': 'Надходження',
            },
        ]

        parser = Mock()
        parser.parse.return_value = parsed_data

        with patch('transactions.services.get_parser_for_bank', return_value=parser):
            process_upload(upload)

        upload.refresh_from_db()

        self.assertEqual(upload.status, 'COMPLETED')
        self.assertEqual(upload.total_transactions, 2)
        self.assertEqual(upload.processed_transactions, 2)
        self.assertIn('Створено: 2', upload.processing_log)

        self.assertEqual(Transaction.objects.filter(source_upload=upload).count(), 2)
        self.assertTrue(Account.objects.filter(user=user, bank=bank).exists())

    def test_kpi_aggregation_with_user_isolation(self):
        user_a = self._create_user('alice', 'alice@example.com')
        user_b = self._create_user('bob', 'bob@example.com')

        bank = Bank.objects.create(name='ПриватБанк')
        account_a = Account.objects.create(
            user=user_a,
            bank=bank,
            account_name='Alice account',
            account_type='BANK',
            currency='UAH',
        )
        account_b = Account.objects.create(
            user=user_b,
            bank=bank,
            account_name='Bob account',
            account_type='BANK',
            currency='UAH',
        )

        now = timezone.now()

        Transaction.objects.create(
            user=user_a,
            account=account_a,
            amount=Decimal('-100.00'),
            description='Groceries',
            transaction_date=now,
        )
        Transaction.objects.create(
            user=user_a,
            account=account_a,
            amount=Decimal('250.00'),
            description='Salary part',
            transaction_date=now,
        )
        Transaction.objects.create(
            user=user_a,
            account=account_a,
            amount=Decimal('-999.00'),
            description='Old expense',
            transaction_date=now - timezone.timedelta(days=40),
        )
        Transaction.objects.create(
            user=user_b,
            account=account_b,
            amount=Decimal('1000.00'),
            description='Foreign user income',
            transaction_date=now,
        )

        repo = TransactionRepository(user_a)
        kpi = repo.get_dashboard_kpi()

        self.assertEqual(kpi['total_expenses'], Decimal('100.00'))
        self.assertEqual(kpi['total_incomes'], Decimal('250.00'))
        self.assertEqual(kpi['balance'], Decimal('150.00'))
        self.assertTrue(kpi['has_transactions'])

    def test_pumb_pdf_parser_with_markdown_table_and_basic_description(self):
        parser = PumbPdfParser()

        table = [
            ['Дата та час операції', 'Опис операції', 'Деталі операції', 'Сума операції'],
            ['2026-03-01 10:00:00', 'Покупка', 'АТБ', '120,50 UAH'],
            ['2026-03-02 12:30:00', 'Зарахування', 'Переказ', '300,00 UAH'],
        ]

        fake_page = Mock()
        fake_page.extract_table.return_value = table

        fake_pdf = Mock()
        fake_pdf.pages = [fake_page]

        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=fake_pdf)
        context_manager.__exit__ = Mock(return_value=False)

        with patch('transactions.parsers.pdfplumber.open', return_value=context_manager):
            result = parser.parse('dummy.pdf')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['amount'], Decimal('-120.50'))
        self.assertEqual(result[1]['amount'], Decimal('300.00'))

        markdown_table = self._to_markdown_table(result)
        summary = self._build_basic_summary(result)

        self.assertIn('| Дата | Опис | Сума |', markdown_table)
        self.assertIn('АТБ', markdown_table)
        self.assertIn('2 транзакції', summary)
        self.assertIn('1 витрат', summary)
        self.assertIn('1 доходів', summary)

    @staticmethod
    def _to_markdown_table(rows):
        lines = [
            '| Дата | Опис | Сума |',
            '|---|---|---:|',
        ]

        for item in rows:
            lines.append(
                f"| {item['date'].date().isoformat()} | {item['description']} | {item['amount']} |"
            )

        return '\n'.join(lines)

    @staticmethod
    def _build_basic_summary(rows):
        expense_count = sum(1 for item in rows if item['amount'] < 0)
        income_count = sum(1 for item in rows if item['amount'] > 0)
        return (
            f"Знайдено {len(rows)} транзакції(й): "
            f"{expense_count} витрат, {income_count} доходів."
        )
