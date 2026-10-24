import importlib
import shutil
import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import clear_url_caches, reverse
from rest_framework.test import APIClient

from accounts.models import Bank

from .models import TransactionUpload
from .uploads import GENERIC_PROCESSING_ERROR, statement_upload_path


class UploadSecurityTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='owner', email='owner@example.com', password='Pass1234!',
        )
        self.other_user = user_model.objects.create_user(
            username='stranger', email='stranger@example.com', password='Pass1234!',
        )
        self.bank = Bank.objects.create(name='UploadBank')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _post_upload(self, name, content=b'date,amount\n', parse_result=None):
        parser = Mock()
        parser.parse.return_value = parse_result or []
        with patch('transactions.services.get_parser_for_bank', return_value=parser), \
                patch('transactions.services.logger.exception'):
            return self.client.post(
                reverse('transactions:api-uploads'),
                {'file': SimpleUploadedFile(name, content), 'bank': self.bank.id},
                format='multipart',
            )

    def _create_upload(self, user, name='statement.csv', content=b'secret-statement'):
        return TransactionUpload.objects.create(
            user=user,
            bank=self.bank,
            file=SimpleUploadedFile(name, content),
        )

    def test_rejects_unsupported_extension(self):
        response = self._post_upload('evil.html', b'<script>alert(1)</script>')

        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.data)
        self.assertFalse(TransactionUpload.objects.exists())

    @override_settings(STATEMENT_MAX_UPLOAD_SIZE=10)
    def test_rejects_oversized_file(self):
        response = self._post_upload('big.csv', b'x' * 11)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TransactionUpload.objects.exists())

    def test_response_hides_storage_path_and_exposes_protected_url(self):
        response = self._post_upload('my statement.csv')

        self.assertEqual(response.status_code, 201)
        self.assertNotIn('file', response.data)
        self.assertEqual(response.data['file_name'], 'my_statement.csv')
        upload_id = response.data['id']
        self.assertTrue(
            response.data['file_url'].endswith(f'/transactions/api/uploads/{upload_id}/file/')
        )

    def test_storage_path_is_not_guessable(self):
        first = statement_upload_path(None, 'statement.csv')
        second = statement_upload_path(None, 'statement.csv')

        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith('bank_statements/'))
        self.assertTrue(first.endswith('/statement.csv'))

    def test_storage_path_survives_suspicious_names(self):
        path = statement_upload_path(None, '..')

        self.assertTrue(path.endswith('/statement'))
        self.assertNotIn('..', path)

    def test_failed_processing_does_not_leak_internal_error(self):
        parser = Mock()
        parser.parse.side_effect = ValueError('/srv/app/media/secret path')
        with patch('transactions.services.get_parser_for_bank', return_value=parser), \
                patch('transactions.services.logger.exception'):
            response = self.client.post(
                reverse('transactions:api-uploads'),
                {'file': SimpleUploadedFile('s.csv', b'a'), 'bank': self.bank.id},
                format='multipart',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'FAILED')
        self.assertEqual(response.data['processing_log'], GENERIC_PROCESSING_ERROR)

    def test_owner_can_download_file(self):
        upload = self._create_upload(self.user)

        response = self.client.get(reverse('transactions:api-upload-file', args=[upload.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'secret-statement')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('no-store', response['Cache-Control'])

    def test_other_user_cannot_download_file(self):
        upload = self._create_upload(self.other_user)

        response = self.client.get(reverse('transactions:api-upload-file', args=[upload.id]))

        self.assertEqual(response.status_code, 404)

    def test_anonymous_cannot_download_file(self):
        upload = self._create_upload(self.user)

        response = APIClient().get(reverse('transactions:api-upload-file', args=[upload.id]))

        self.assertEqual(response.status_code, 401)

    def test_media_is_not_served_directly_even_in_debug(self):
        import core.urls

        try:
            with override_settings(DEBUG=True):
                urlconf = importlib.reload(core.urls)
                patterns = [str(p.pattern) for p in urlconf.urlpatterns]
        finally:
            importlib.reload(core.urls)
            clear_url_caches()

        self.assertFalse([p for p in patterns if 'media' in p])
