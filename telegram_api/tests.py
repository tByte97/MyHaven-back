from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Bank, Account
from budgets.models import Budget
from transactions.models import Category, Transaction


class TelegramApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tg_user',
            email='tg_user@example.com',
            password='Pass1234!',
            telegram_user_id=987654321,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_TELEGRAM_USER_ID='987654321')

    def _create_category(self, name='Food', category_type='EXPENSE', system=False):
        return Category.objects.create(
            user=None if system else self.user,
            name=name,
            type=category_type,
            is_system=system,
        )

    def _create_account(self, name='Main'):
        bank, _ = Bank.objects.get_or_create(name='TestBank')
        return Account.objects.create(
            user=self.user,
            bank=bank,
            account_name=name,
            account_type='BANK',
            currency='UAH',
        )

    def test_health_endpoint(self):
        response = self.client.get('/api/telegram/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['telegram_user_id'], self.user.telegram_user_id)

    def test_telegram_api_rejects_missing_telegram_header(self):
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.get('/api/telegram/health/')

        self.assertEqual(response.status_code, 403)

    def test_telegram_api_rejects_mismatched_telegram_header(self):
        self.client.credentials(HTTP_X_TELEGRAM_USER_ID='111')

        response = self.client.get('/api/telegram/health/')

        self.assertEqual(response.status_code, 403)

    def test_transaction_create_and_list(self):
        category = self._create_category()
        payload = {
            'amount': '-12.50',
            'description': 'Snack',
            'transaction_date': timezone.now().isoformat(),
            'category': category.id,
        }

        response = self.client.post('/api/telegram/transactions/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['source'], 'telegram')

        response = self.client.get('/api/telegram/transactions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        transaction = Transaction.objects.get()
        self.assertEqual(transaction.source, 'telegram')
        self.assertTrue(Account.objects.filter(user=self.user, account_name='Telegram').exists())

    def test_transaction_create_resolves_category_name(self):
        category = self._create_category(name='Кафе та ресторани')
        category.keywords = ['їжа', 'кафе']
        category.save()
        payload = {
            'amount': '-250.00',
            'description': 'Кава і сендвіч',
            'transaction_date': timezone.now().isoformat(),
            'category_name': 'Йіжа',
        }

        response = self.client.post('/api/telegram/transactions/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['category']['id'], category.id)

    def test_transaction_create_resolves_spoken_food_inflections(self):
        category = self._create_category(name='Кафе та ресторани')
        category.keywords = ['їжа', 'кафе']
        category.save()

        for spoken_category in ('їжу', 'Йізя', 'ізью'):
            with self.subTest(spoken_category=spoken_category):
                payload = {
                    'amount': '-250.00',
                    'description': 'Додає витрату в 250 гривень на їжу вчора.',
                    'transaction_date': timezone.now().isoformat(),
                    'category_name': spoken_category,
                }

                response = self.client.post('/api/telegram/transactions/', payload, format='json')

                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data['category']['id'], category.id)

    def test_dashboard_summary(self):
        account = self._create_account()
        category = self._create_category()
        Transaction.objects.create(
            account=account,
            category=category,
            amount=Decimal('-50.00'),
            description='Groceries',
            transaction_date=timezone.now(),
        )

        response = self.client.get('/api/telegram/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_expenses', response.data)
        self.assertIn('recent_transactions', response.data)

    def test_statistics_and_calendar_endpoints(self):
        account = self._create_account()
        category = self._create_category()
        tx_date = timezone.now().replace(day=15)
        Transaction.objects.create(
            account=account,
            category=category,
            amount=Decimal('-75.00'),
            description='Taxi',
            transaction_date=tx_date,
        )

        statistics_response = self.client.get('/api/telegram/statistics/?months=3')
        self.assertEqual(statistics_response.status_code, 200)
        self.assertEqual(statistics_response.data['requested_months'], 3)
        self.assertIn('monthly_summary', statistics_response.data)

        calendar_response = self.client.get(
            f'/api/telegram/calendar/?year={tx_date.year}&month={tx_date.month}'
        )
        self.assertEqual(calendar_response.status_code, 200)
        self.assertEqual(calendar_response.data['year'], tx_date.year)
        self.assertEqual(calendar_response.data['month'], tx_date.month)

        day_response = self.client.get(
            f'/api/telegram/calendar/{tx_date.year}/{tx_date.month}/{tx_date.day}/'
        )
        self.assertEqual(day_response.status_code, 200)
        self.assertEqual(len(day_response.data), 1)

    def test_categories_include_system_and_user(self):
        self._create_category(name='System', system=True)
        self._create_category(name='User', system=False)

        response = self.client.get('/api/telegram/categories/')
        self.assertEqual(response.status_code, 200)
        names = {item['name'] for item in response.data}
        self.assertIn('System', names)
        self.assertIn('User', names)

    def test_budget_create_and_list(self):
        category = self._create_category()
        payload = {
            'category': category.id,
            'month': timezone.now().date().replace(day=1).isoformat(),
            'amount': '300.00',
        }

        response = self.client.post('/api/telegram/budgets/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Budget.objects.count(), 1)

        response = self.client.get('/api/telegram/budgets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_budget_create_resolves_category_name(self):
        category = self._create_category(name='Продукти')
        payload = {
            'category_name': 'продукти',
            'month': timezone.now().date().replace(day=1).isoformat(),
            'amount': '3000.00',
        }

        response = self.client.post('/api/telegram/budgets/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Budget.objects.get().category_id, category.id)

    def test_transaction_detail_update_and_delete(self):
        account = self._create_account()
        category = self._create_category()
        transaction = Transaction.objects.create(
            account=account,
            category=category,
            amount=Decimal('-20.00'),
            description='Old description',
            transaction_date=timezone.now(),
        )

        detail_response = self.client.get(f'/api/telegram/transactions/{transaction.id}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['id'], transaction.id)

        update_response = self.client.patch(
            f'/api/telegram/transactions/{transaction.id}/',
            {'description': 'Updated description'},
            format='json',
        )
        self.assertEqual(update_response.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, 'Updated description')

        delete_response = self.client.delete(f'/api/telegram/transactions/{transaction.id}/')
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_budget_detail_update_and_delete(self):
        category = self._create_category()
        budget = Budget.objects.create(
            user=self.user,
            category=category,
            month=timezone.now().date().replace(day=1),
            amount=Decimal('300.00'),
        )

        detail_response = self.client.get(f'/api/telegram/budgets/{budget.id}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['id'], budget.id)

        update_response = self.client.patch(
            f'/api/telegram/budgets/{budget.id}/',
            {'amount': '450.00'},
            format='json',
        )
        self.assertEqual(update_response.status_code, 200)
        budget.refresh_from_db()
        self.assertEqual(budget.amount, Decimal('450.00'))

        delete_response = self.client.delete(f'/api/telegram/budgets/{budget.id}/')
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Budget.objects.filter(id=budget.id).exists())

    def test_upload_statement_with_bank_name_processes_file(self):
        bank = Bank.objects.create(name='Monobank')
        file = SimpleUploadedFile(
            'statement.csv',
            b'date,amount,description\n2026-05-01,-12,Coffee\n',
            content_type='text/csv',
        )

        with patch('telegram_api.views.process_upload') as process_upload:
            response = self.client.post(
                '/api/telegram/uploads/',
                {'bank_name': bank.name, 'file': file},
                format='multipart',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['bank_name'], bank.name)
        process_upload.assert_called_once()
