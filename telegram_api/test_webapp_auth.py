import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

BOT_TOKEN = '123456:TEST-TOKEN'


def signed_init_data(user_id, bot_token=BOT_TOKEN, auth_date=None, **extra):
    """initData, підписаний як у Telegram (WebAppData → HMAC-SHA256)."""
    fields = {
        'auth_date': str(int(time.time()) if auth_date is None else auth_date),
        'query_id': 'AAHdF6IQAAAAAN0XohDhrOrc',
        'user': json.dumps({'id': user_id, 'first_name': 'Тест'}, ensure_ascii=False),
        **extra,
    }
    check_string = '\n'.join(f'{key}={fields[key]}' for key in sorted(fields))
    secret = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN, TELEGRAM_WEBAPP_AUTH_MAX_AGE=3600)
class TelegramWebAppAuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = get_user_model().objects.create_user(
            username='webapp', email='webapp@example.com', password='Pass1234!',
            telegram_user_id=777,
        )
        self.client = APIClient()

    def _auth(self, init_data):
        return self.client.post(
            '/api/telegram/webapp-auth/', {'init_data': init_data}, format='json',
        )

    def test_valid_init_data_returns_access_token_for_linked_user(self):
        response = self._auth(signed_init_data(777))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('refresh', response.data)
        me = APIClient()
        me.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(me.get('/api/users/me/').data['username'], 'webapp')

    def test_tampered_user_id_is_rejected(self):
        init_data = signed_init_data(777).replace('%22id%22%3A+777', '%22id%22%3A+778')
        get_user_model().objects.create_user(
            username='victim', email='victim@example.com', password='Pass1234!',
            telegram_user_id=778,
        )

        response = self._auth(init_data)

        self.assertEqual(response.status_code, 401)

    def test_data_signed_with_other_bot_token_is_rejected(self):
        response = self._auth(signed_init_data(777, bot_token='999:OTHER'))

        self.assertEqual(response.status_code, 401)

    def test_expired_init_data_is_rejected(self):
        response = self._auth(signed_init_data(777, auth_date=int(time.time()) - 3601))

        self.assertEqual(response.status_code, 401)

    def test_unlinked_telegram_user_is_forbidden(self):
        response = self._auth(signed_init_data(12345))

        self.assertEqual(response.status_code, 403)

    def test_inactive_user_is_forbidden(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        response = self._auth(signed_init_data(777))

        self.assertEqual(response.status_code, 403)

    def test_missing_or_malformed_init_data_is_rejected(self):
        self.assertEqual(self._auth('').status_code, 401)
        self.assertEqual(self._auth('not a query string').status_code, 401)
        self.assertEqual(self._auth('auth_date=1&user=%7B%7D').status_code, 401)

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_disabled_without_bot_token(self):
        response = self._auth(signed_init_data(777, bot_token=''))

        self.assertEqual(response.status_code, 401)

    def test_extra_signed_fields_are_part_of_signature(self):
        init_data = signed_init_data(777, signature='abc', chat_type='private')

        self.assertEqual(self._auth(init_data).status_code, 200)
        self.assertEqual(
            self._auth(init_data.replace('chat_type=private', 'chat_type=group')).status_code,
            401,
        )
