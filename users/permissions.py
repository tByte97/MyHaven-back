import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission

BOT_SECRET_HEADER = 'X-MyHaven-Bot-Secret'


class IsTelegramBot(BasePermission):
    """
    Запит від нашого Telegram-бота: спільний секрет у заголовку.
    Без нього telegram_user_id у тілі чи X-Telegram-User-Id міг би
    підставити будь-хто. Якщо секрет не налаштований — доступ закрито.
    """

    message = 'Telegram bot credentials are missing or invalid.'

    def has_permission(self, request, view):
        expected = getattr(settings, 'TELEGRAM_BOT_API_SECRET', '')
        provided = request.headers.get(BOT_SECRET_HEADER, '')
        if not expected or not provided:
            return False
        return hmac.compare_digest(provided.encode('utf-8'), expected.encode('utf-8'))
