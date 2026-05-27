from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
import pyotp
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

	def test_telegram_register_creates_user_and_links_profile(self):
		client = APIClient()
		payload = {
			'username': 'tgnewuser',
			'email': 'tgnewuser@example.com',
			'password': 'Pass1234!',
			'first_name': 'Iryna',
			'last_name': 'Koval',
			'language': 'uk',
			'currency': 'UAH',
			'display_currency': 'UAH',
			'theme': 'dark',
			'tracking_sources': ['card', 'bank'],
			'telegram_user_id': 555123,
			'telegram_username': 'tg_new_user',
		}

		response = client.post('/api/users/telegram/register/', payload, format='json')

		self.assertEqual(response.status_code, 201)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

		created_user = get_user_model().objects.get(username='tgnewuser')
		self.assertEqual(created_user.telegram_user_id, 555123)
		self.assertEqual(created_user.telegram_username, 'tg_new_user')
		self.assertEqual(created_user.display_currency, 'UAH')
		self.assertEqual(created_user.tracking_sources, ['card', 'bank'])

	def test_telegram_register_rejects_taken_telegram_user_id(self):
		existing_user = get_user_model().objects.create_user(
			username='linked_owner',
			email='linked_owner@example.com',
			password='Pass1234!',
			telegram_user_id=777888,
		)
		self.assertEqual(existing_user.telegram_user_id, 777888)

		client = APIClient()
		payload = {
			'username': 'anotheruser',
			'email': 'anotheruser@example.com',
			'password': 'Pass1234!',
			'language': 'uk',
			'currency': 'UAH',
			'display_currency': 'UAH',
			'theme': 'dark',
			'tracking_sources': ['card'],
			'telegram_user_id': 777888,
			'telegram_username': 'collision_user',
		}

		response = client.post('/api/users/telegram/register/', payload, format='json')

		self.assertEqual(response.status_code, 409)
		self.assertFalse(get_user_model().objects.filter(username='anotheruser').exists())

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

	def test_link_code_cannot_be_reused(self):
		client = APIClient()
		client.force_authenticate(user=self.user)
		response = client.post('/api/users/telegram/link-code/')
		self.assertEqual(response.status_code, 200)
		secret = response.data['secret']

		client.force_authenticate(user=None)
		first_response = client.post(
			'/api/users/telegram/link/',
			{'secret': secret, 'telegram_user_id': 123},
			format='json',
		)
		second_response = client.post(
			'/api/users/telegram/link/',
			{'secret': secret, 'telegram_user_id': 456},
			format='json',
		)

		self.assertEqual(first_response.status_code, 200)
		self.assertEqual(second_response.status_code, 400)

	def test_link_exchange_rejects_telegram_id_already_bound_to_other_user(self):
		other_user = get_user_model().objects.create_user(
			username='linked_elsewhere',
			email='linked_elsewhere@example.com',
			password='Pass1234!',
			telegram_user_id=999,
		)
		self.assertEqual(other_user.telegram_user_id, 999)

		client = APIClient()
		client.force_authenticate(user=self.user)
		response = client.post('/api/users/telegram/link-code/')
		self.assertEqual(response.status_code, 200)
		secret = response.data['secret']

		client.force_authenticate(user=None)
		response = client.post(
			'/api/users/telegram/link/',
			{'secret': secret, 'telegram_user_id': 999},
			format='json',
		)

		self.assertEqual(response.status_code, 409)

	def test_unlink_telegram_clears_profile_and_pending_codes(self):
		client = APIClient()
		self.user.telegram_user_id = 123456789
		self.user.telegram_username = 'tester'
		self.user.telegram_notifications = True
		self.user.save(update_fields=[
			'telegram_user_id',
			'telegram_username',
			'telegram_notifications',
		])
		client.force_authenticate(user=self.user)
		code_response = client.post('/api/users/telegram/link-code/')
		self.assertEqual(code_response.status_code, 200)

		response = client.delete('/api/users/telegram/unlink/')
		self.assertEqual(response.status_code, 200)

		self.user.refresh_from_db()
		self.assertIsNone(self.user.telegram_user_id)
		self.assertIsNone(self.user.telegram_username)
		self.assertFalse(self.user.telegram_notifications)
		self.assertFalse(self.user.telegram_link_codes.filter(used_at__isnull=True).exists())


class AuthFlowTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='secureuser',
			email='secure@example.com',
			password='Pass1234!',
			totp_secret=pyotp.random_base32(),
			totp_enabled=True,
		)
		self.client = APIClient()

	def test_login_requires_totp_for_protected_user(self):
		response = self.client.post(
			'/api/users/auth/login/',
			{'username': 'secureuser', 'password': 'Pass1234!'},
			format='json',
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data['requires_totp'])
		self.assertIn('login_token', response.data)

	def test_login_totp_verification_returns_tokens(self):
		login_response = self.client.post(
			'/api/users/auth/login/',
			{'username': 'secureuser', 'password': 'Pass1234!'},
			format='json',
		)
		code = pyotp.TOTP(self.user.totp_secret).now()
		verify_response = self.client.post(
			'/api/users/auth/verify-totp/',
			{'login_token': login_response.data['login_token'], 'code': code},
			format='json',
		)
		self.assertEqual(verify_response.status_code, 200)
		self.assertIn('access', verify_response.data)
		self.assertIn('refresh', verify_response.data)


class ProfileSecurityNotificationsTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='notifyuser',
			email='notify@example.com',
			password='Pass1234!',
		)
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

	@override_settings(EMAIL_HOST='smtp.example.com', DEFAULT_FROM_EMAIL='noreply@example.com')
	def test_change_password_sends_security_email(self):
		response = self.client.post(
			'/api/users/change-password/',
			{'old_password': 'Pass1234!', 'new_password': 'NewPass1234!'},
			format='json',
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('password changed', mail.outbox[0].subject.lower())

	@override_settings(EMAIL_HOST='smtp.example.com', DEFAULT_FROM_EMAIL='noreply@example.com')
	def test_change_email_sends_notifications_to_old_and_new_email(self):
		response = self.client.patch(
			'/api/users/profile/',
			{'email': 'newnotify@example.com'},
			format='json',
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 2)
		recipients = sorted(mail.outbox[0].to + mail.outbox[1].to)
		self.assertEqual(recipients, ['newnotify@example.com', 'notify@example.com'])

	def test_preferences_reject_empty_tracking_sources(self):
		response = self.client.patch(
			'/api/users/preferences/',
			{'tracking_sources': []},
			format='json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('tracking_sources', response.data)
