"""
Правила зберігання банківських виписок: шлях у storage, валідація файлу
та безпечні повідомлення про помилки обробки для користувача.
"""
import os
import uuid

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation, ValidationError
from django.utils import timezone
from django.utils.text import get_valid_filename

ALLOWED_STATEMENT_EXTENSIONS = ('.csv', '.xls', '.xlsx', '.pdf')

GENERIC_PROCESSING_ERROR = (
    'Не вдалося обробити файл. Перевірте, що обрано правильний банк '
    'і формат виписки.'
)


class UploadProcessingError(Exception):
    """Помилка обробки, текст якої безпечно показувати користувачу."""


def statement_upload_path(instance, filename):
    """
    bank_statements/<рік>/<місяць>/<випадковий каталог>/<очищена назва>.
    Випадковий каталог робить шлях невгадуваним, назва зберігається для показу.
    """
    now = timezone.now()
    try:
        safe_name = get_valid_filename(os.path.basename(filename))
    except SuspiciousFileOperation:
        safe_name = 'statement'
    return f'bank_statements/{now:%Y/%m}/{uuid.uuid4().hex}/{safe_name}'


def max_statement_size():
    return getattr(settings, 'STATEMENT_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)


def validate_statement_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_STATEMENT_EXTENSIONS:
        raise ValidationError(
            'Непідтримуваний тип файлу. Дозволено: %(allowed)s.',
            params={'allowed': ', '.join(ALLOWED_STATEMENT_EXTENSIONS)},
            code='invalid_extension',
        )
    limit = max_statement_size()
    if file.size is not None and file.size > limit:
        raise ValidationError(
            'Файл завеликий. Максимум — %(limit)d МБ.',
            params={'limit': limit // (1024 * 1024)},
            code='file_too_large',
        )


def display_name(upload):
    """Назва файлу без службового шляху в storage."""
    return os.path.basename(upload.file.name) if upload.file else None


def public_error_message(exc):
    """Текст для processing_log: без шляхів на сервері та внутрішніх винятків."""
    if isinstance(exc, UploadProcessingError):
        return str(exc)
    return GENERIC_PROCESSING_ERROR
