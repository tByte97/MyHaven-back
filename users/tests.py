from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Account, Bank
from budgets.models import Budget
from transactions.models import Category, Transaction, TransactionUpload
from users.services import AccountDeletionService, ExportService


class UserServicesTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='owner',
			email='owner@example.com',
			password='Pass1234!',
		)

	def _create_category(self):
		return Category.objects.create(
			user=self.user,
			name='Food',
			type='EXPENSE',
			keywords=['shop'],
		)

	def test_export_service_contains_expected_sections(self):
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
			amount=Decimal('-25.50'),
			description='Lunch',
			transaction_date=timezone.now(),
		)
		Budget.objects.create(
			user=self.user,
			category=category,
			month=timezone.now().date().replace(day=1),
			amount=Decimal('500.00'),
		)
		TransactionUpload.objects.create(
			user=self.user,
			bank=bank,
			file=SimpleUploadedFile('statement.csv', b'data', content_type='text/csv'),
		)

		payload = ExportService.export_all_data(self.user)

		self.assertIn('profile', payload)
		self.assertIn('preferences', payload)
		self.assertIn('notifications', payload)
		self.assertEqual(len(payload['transactions']), 1)
		self.assertEqual(len(payload['budgets']), 1)
		self.assertEqual(len(payload['uploads']), 1)
		self.assertNotIn('telegram_user_id', payload['profile'])
		self.assertNotIn('telegram_username', payload['profile'])

	def test_account_deletion_service_removes_user_data(self):
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
			amount=Decimal('-10.00'),
			description='Coffee',
			transaction_date=timezone.now(),
		)
		Budget.objects.create(
			user=self.user,
			category=category,
			month=timezone.now().date().replace(day=1),
			amount=Decimal('100.00'),
		)
		TransactionUpload.objects.create(
			user=self.user,
			bank=bank,
			file=SimpleUploadedFile('statement.csv', b'data', content_type='text/csv'),
		)

		AccountDeletionService.delete_user_account(self.user)

		self.assertFalse(get_user_model().objects.filter(id=self.user.id).exists())
		self.assertEqual(Transaction.objects.count(), 0)
		self.assertEqual(Budget.objects.count(), 0)
		self.assertEqual(TransactionUpload.objects.count(), 0)


class TelegramLinkTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='linkuser',
			email='linkuser@example.com',
			password='Pass1234!',
		)

	def test_link_code_exchange_returns_tokens(self):
		client = APIClient()
		client.force_authenticate(user=self.user)
		response = client.post('/api/users/telegram/link-code/')
		self.assertEqual(response.status_code, 200)
		secret = response.data['secret']

		client.force_authenticate(user=None)
		payload = {
			'secret': secret,
			'telegram_user_id': 123456789,
			'telegram_username': 'tester',
		}
		response = client.post('/api/users/telegram/link/', payload, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

		self.user.refresh_from_db()
		self.assertEqual(self.user.telegram_user_id, 123456789)
		self.assertEqual(self.user.telegram_username, 'tester')
