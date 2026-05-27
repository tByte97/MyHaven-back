from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, Bank

from .categorization import CategoryMatcher, find_category_by_name
from .models import Category, Transaction, TransactionUpload
from .parsers import BankStatementParser
from .repositories import TransactionRepository
from .services import process_upload


class TransactionCriticalPathTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tx_user',
            email='tx_user@example.com',
            password='Pass1234!',
        )
        self.other_user = get_user_model().objects.create_user(
            username='other_tx_user',
            email='other_tx_user@example.com',
            password='Pass1234!',
        )
        self.bank = Bank.objects.create(name='CriticalBank')
        self.account = Account.objects.create(
            user=self.user,
            bank=self.bank,
            account_name='Main',
            account_type='BANK',
            currency='UAH',
        )
        self.other_account = Account.objects.create(
            user=self.other_user,
            bank=self.bank,
            account_name='Other',
            account_type='BANK',
            currency='UAH',
        )
        self.food = Category.objects.create(
            user=self.user,
            name='Кафе та ресторани',
            type='EXPENSE',
            keywords=['їжа', 'кафе'],
        )
        self.salary = Category.objects.create(
            user=self.user,
            name='Зарплата',
            type='INCOME',
            keywords=['зарплата'],
        )

    def test_find_category_by_name_resolves_speech_variants_and_keywords(self):
        self.assertEqual(find_category_by_name(self.user, 'Йізя'), self.food)
        self.assertEqual(find_category_by_name(self.user, 'їжу'), self.food)
        self.assertEqual(find_category_by_name(self.user, 'кафе'), self.food)
        self.assertIsNone(find_category_by_name(self.user, 'невідома категорія'))

    def test_category_matcher_uses_keywords_and_income_expense_direction(self):
        matcher = CategoryMatcher(self.user)

        expense_category, expense_score = matcher.match(
            description='Оплата в кафе біля офісу',
            amount=Decimal('-120.00'),
        )
        income_category, income_score = matcher.match(
            description='Нарахована зарплата',
            amount=Decimal('1000.00'),
        )

        self.assertEqual(expense_category, self.food)
        self.assertGreaterEqual(expense_score, 1.0)
        self.assertEqual(income_category, self.salary)
        self.assertGreaterEqual(income_score, 1.0)

    def test_repository_filters_transactions_and_keeps_user_isolation(self):
        now = timezone.now()
        old_date = now - timezone.timedelta(days=10)
        matching = Transaction.objects.create(
            account=self.account,
            category=self.food,
            amount=Decimal('-50.00'),
            description='Coffee with team',
            transaction_date=now,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.salary,
            amount=Decimal('500.00'),
            description='Salary',
            transaction_date=now,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.food,
            amount=Decimal('-25.00'),
            description='Old groceries',
            transaction_date=old_date,
        )
        Transaction.objects.create(
            account=self.other_account,
            category=self.food,
            amount=Decimal('-999.00'),
            description='Foreign user transaction',
            transaction_date=now,
        )

        repo = TransactionRepository(self.user)
        filtered = repo.get_filtered_transactions(
            category_id=self.food.id,
            transaction_type='expense',
            date_from=now.date().isoformat(),
            search='Coffee',
        )

        self.assertEqual(list(filtered), [matching])

    def test_repository_calendar_data_and_day_transactions(self):
        tx_date = timezone.now().replace(day=12)
        Transaction.objects.create(
            account=self.account,
            category=self.food,
            amount=Decimal('-40.00'),
            description='Taxi',
            transaction_date=tx_date,
        )
        Transaction.objects.create(
            account=self.account,
            category=self.salary,
            amount=Decimal('100.00'),
            description='Bonus',
            transaction_date=tx_date,
        )

        repo = TransactionRepository(self.user)
        calendar_rows = list(repo.get_calendar_data(tx_date.year, tx_date.month))
        day_transactions = list(
            repo.get_calendar_day_transactions(tx_date.year, tx_date.month, tx_date.day)
        )

        self.assertEqual(len(calendar_rows), 1)
        self.assertEqual(abs(calendar_rows[0]['expenses']), Decimal('40.00'))
        self.assertEqual(calendar_rows[0]['incomes'], Decimal('100.00'))
        self.assertEqual(len(day_transactions), 2)

    def test_process_upload_creates_transactions_and_skips_duplicates(self):
        upload = TransactionUpload.objects.create(
            user=self.user,
            bank=self.bank,
            file=SimpleUploadedFile('statement.csv', b'dummy', content_type='text/csv'),
        )
        tx_date = timezone.now()
        parsed_data = [
            {
                'date': tx_date,
                'amount': Decimal('-120.50'),
                'description': 'Кава',
                'bank_category': 'Cafe',
            },
            {
                'date': tx_date,
                'amount': Decimal('-120.50'),
                'description': 'Кава',
                'bank_category': 'Cafe',
            },
        ]
        parser = Mock()
        parser.parse.return_value = parsed_data

        with patch('transactions.services.get_parser_for_bank', return_value=parser):
            process_upload(upload)

        upload.refresh_from_db()
        self.assertEqual(upload.status, 'COMPLETED')
        self.assertEqual(upload.total_transactions, 2)
        self.assertEqual(upload.processed_transactions, 1)
        self.assertIn('Пропущено', upload.processing_log)
        self.assertEqual(Transaction.objects.filter(source_upload=upload).count(), 1)

    def test_process_upload_marks_failed_and_reraises_parser_errors(self):
        upload = TransactionUpload.objects.create(
            user=self.user,
            bank=self.bank,
            file=SimpleUploadedFile('statement.csv', b'dummy', content_type='text/csv'),
        )
        parser = Mock()
        parser.parse.side_effect = ValueError('broken parser')

        with patch('transactions.services.get_parser_for_bank', return_value=parser):
            with patch('transactions.services.logger.exception'):
                with self.assertRaises(ValueError):
                    process_upload(upload)

        upload.refresh_from_db()
        self.assertEqual(upload.status, 'FAILED')
        self.assertIn('broken parser', upload.processing_log)

    def test_clean_amount_handles_bank_formatting(self):
        self.assertEqual(BankStatementParser.clean_amount('1 234,56 UAH'), Decimal('1234.56'))
        self.assertEqual(BankStatementParser.clean_amount('-99,10'), Decimal('-99.10'))
        self.assertEqual(BankStatementParser.clean_amount('not amount'), Decimal('0'))
