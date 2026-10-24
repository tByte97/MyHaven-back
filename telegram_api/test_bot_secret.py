from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

BOT_SECRET = 'test-bot-secret'


@override_settings(TELEGRAM_BOT_API_SECRET=BOT_SECRET)
class TelegramBotSecretTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tg_owner', email='tg_owner@example.com', password='Pass1234!',
            telegram_user_id=5005,
        )

    def _register_payload(self, telegram_user_id=7007):
        return {
            'username': 'squatter',
            'email': 'squatter@example.com',
            'password': 'Pass1234!xyz',
            'tracking_sources': ['card'],
            'telegram_user_id': telegram_user_id,
        }

    def test_telegram_register_without_bot_secret_is_forbidden(self):
        response = APIClient().post(
            '/api/users/telegram/register/', self._register_payload(), format='json',
        )

        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(get_user_model().objects.filter(username='squatter').exists())

    def test_telegram_register_with_wrong_bot_secret_is_forbidden(self):
        response = APIClient().post(
            '/api/users/telegram/register/', self._register_payload(), format='json',
            HTTP_X_MYHAVEN_BOT_SECRET='wrong',
        )

        self.assertIn(response.status_code, (401, 403))

    def test_telegram_register_with_bot_secret_works(self):
        response = APIClient().post(
            '/api/users/telegram/register/', self._register_payload(), format='json',
            HTTP_X_MYHAVEN_BOT_SECRET=BOT_SECRET,
        )

        self.assertEqual(response.status_code, 201)

    def test_link_exchange_without_bot_secret_is_forbidden(self):
        response = APIClient().post(
            '/api/users/telegram/link/',
            {'secret': 'whatever', 'telegram_user_id': 1},
            format='json',
        )

        self.assertIn(response.status_code, (401, 403))

    def test_telegram_api_with_stolen_jwt_but_no_bot_secret_is_forbidden(self):
        client = APIClient()
        client.force_authenticate(self.user)
        client.credentials(HTTP_X_TELEGRAM_USER_ID='5005')

        response = client.get('/api/telegram/dashboard/')

        self.assertIn(response.status_code, (401, 403))

    @override_settings(TELEGRAM_BOT_API_SECRET='')
    def test_endpoints_are_closed_when_secret_is_not_configured(self):
        response = APIClient().post(
            '/api/users/telegram/register/', self._register_payload(), format='json',
            HTTP_X_MYHAVEN_BOT_SECRET='',
        )

        self.assertIn(response.status_code, (401, 403))
