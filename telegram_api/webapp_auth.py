"""
Перевірка Telegram WebApp initData:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class WebAppAuthError(Exception):
    pass


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int, now=None) -> dict:
    """Повертає об'єкт user з initData або кидає WebAppAuthError."""
    if not init_data or not bot_token:
        raise WebAppAuthError('init_data is missing')

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError as exc:
        raise WebAppAuthError('init_data is malformed') from exc

    received_hash = pairs.pop('hash', '')
    if not received_hash:
        raise WebAppAuthError('hash is missing')

    data_check_string = '\n'.join(f'{key}={pairs[key]}' for key in sorted(pairs))
    secret_key = hmac.new(b'WebAppData', bot_token.encode('utf-8'), hashlib.sha256).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode('utf-8'), hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise WebAppAuthError('hash mismatch')

    try:
        auth_date = int(pairs.get('auth_date', ''))
    except ValueError as exc:
        raise WebAppAuthError('auth_date is missing') from exc
    now = time.time() if now is None else now
    if now - auth_date > max_age_seconds:
        raise WebAppAuthError('init_data is expired')

    try:
        user = json.loads(pairs.get('user', ''))
        int(user['id'])
    except (ValueError, TypeError, KeyError) as exc:
        raise WebAppAuthError('user is missing') from exc
    return user
