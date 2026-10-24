"""
Обмеження частоти запитів до чутливих ендпоінтів (підбір паролів, TOTP-кодів,
link-кодів, масові реєстрації). Ліміти задаються в REST_FRAMEWORK
['DEFAULT_THROTTLE_RATES'] і зберігаються в Django cache: для кількох
воркерів потрібен спільний cache (Redis тощо), LocMemCache рахує окремо
в кожному процесі.
"""
from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class TelegramIdentityThrottle(ScopedRateThrottle):
    """
    Запити Telegram-реєстрації та обміну link-коду приходять з IP бота,
    тому лише IP поділив би один ліміт між усіма користувачами Telegram.
    Ключ — IP + telegram_user_id із тіла запиту (йому можна довіряти:
    ці ендпоінти вимагають секрет бота, див. users.permissions).
    """

    def get_cache_key(self, request, view):
        telegram_user_id = str(request.data.get('telegram_user_id', ''))[:32]
        ident = f'{self.get_ident(request)}:{telegram_user_id}'
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class FormRateThrottle(SimpleRateThrottle):
    """
    Те саме обмеження для Django template views (не DRF). Ключ збігається
    з ScopedRateThrottle для анонімів, тож форма й API мають спільний ліміт.
    """

    def __init__(self, scope):
        self.scope = scope
        super().__init__()

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


def form_request_allowed(request, scope):
    return FormRateThrottle(scope).allow_request(request, None)
