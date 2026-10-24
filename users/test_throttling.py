from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle


def allowed_requests(scope):
    """Скільки запитів дозволяє ліміт scope у поточному вікні."""
    rate = SimpleRateThrottle.THROTTLE_RATES[scope]
    return int(rate.split('/')[0])


class AuthThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = get_user_model().objects.create_user(
            username='victim', email='victim@example.com', password='Pass1234!',
        )
        self.client = APIClient()

    def _exhaust(self, scope, send):
        for _ in range(allowed_requests(scope)):
            response = send()
            self.assertNotEqual(response.status_code, 429)
        return send()

    def test_login_bruteforce_is_throttled(self):
        response = self._exhaust('auth', lambda: self.client.post(
            '/api/users/auth/login/',
            {'username': 'victim', 'password': 'wrong'},
            format='json',
        ))

        self.assertEqual(response.status_code, 429)

    def test_login_form_shares_limit_with_api(self):
        for _ in range(allowed_requests('auth')):
            self.client.post(
                '/api/users/auth/login/',
                {'username': 'victim', 'password': 'wrong'},
                format='json',
            )

        response = Client().post('/login/', {'username': 'victim', 'password': 'Pass1234!'})

        self.assertEqual(response.status_code, 429)
        self.assertNotIn('_auth_user_id', response.wsgi_request.session)

    def test_login_totp_code_bruteforce_is_throttled(self):
        response = self._exhaust('totp', lambda: self.client.post(
            '/api/users/auth/verify-totp/',
            {'login_token': 'invalid', 'code': '000000'},
            format='json',
        ))

        self.assertEqual(response.status_code, 429)

    def test_registration_is_throttled(self):
        response = self._exhaust('register', lambda: self.client.post(
            '/api/users/register/', {}, format='json',
        ))

        self.assertEqual(response.status_code, 429)

    def test_token_refresh_is_throttled(self):
        response = self._exhaust('token_refresh', lambda: self.client.post(
            '/api/token/refresh/', {'refresh': 'invalid'}, format='json',
        ))

        self.assertEqual(response.status_code, 429)

    def test_password_check_for_logged_in_user_is_throttled(self):
        self.client.force_authenticate(self.user)

        response = self._exhaust('password', lambda: self.client.post(
            '/api/users/change-password/',
            {'old_password': 'wrong', 'new_password': 'NewPass1234!'},
            format='json',
        ))

        self.assertEqual(response.status_code, 429)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Pass1234!'))

    def test_telegram_link_limit_is_per_telegram_user(self):
        def exchange(telegram_user_id):
            return self.client.post(
                '/api/users/telegram/link/',
                {'secret': 'guess', 'telegram_user_id': telegram_user_id},
                format='json',
            )

        blocked = self._exhaust('telegram', lambda: exchange(111))
        other_user = exchange(222)

        self.assertEqual(blocked.status_code, 429)
        # Запити бота йдуть з однієї IP: ліміт одного користувача Telegram
        # не повинен блокувати інших.
        self.assertEqual(other_user.status_code, 400)
