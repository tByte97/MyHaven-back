from decimal import Decimal

from django.contrib.auth import get_user_model
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
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _create_category(self, name='Food', category_type='EXPENSE', system=False):
        return Category.objects.create(
            user=None if system else self.user,
            name=name,
            type=category_type,
            is_system=system,
        )

    def test_health_endpoint(self):
        response = self.client.get('/api/telegram/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')

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

    def test_dashboard_summary(self):
        bank = Bank.objects.create(name='TestBank')
        account = Account.objects.create(
            user=self.user,
            bank=bank,
            account_name='Main',
            account_type='BANK',
            currency='UAH',
        )
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
