from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from prospects.models import AgentLog
from prospects.services.email_sender import send_message_via_brevo
from .factories import make_lead, make_message


def fake_response(status_code, text=''):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if status_code >= 300:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    return resp


@override_settings(
    BREVO_API_KEY='test-key',
    BREVO_SENDER_EMAIL='sender@example.com',
    BREVO_SENDER_NAME='Test Sender',
    PUBLIC_BACKEND_URL='http://testserver',
)
class SendMessageViaBrevoTests(TestCase):
    def setUp(self):
        self.lead = make_lead(email='dest@example.com', first_name='Marie')
        self.message = make_message(self.lead, status='DRAFT', body='Contenu du message.')

    @patch('prospects.services.email_sender.requests.post')
    def test_successful_send_updates_message_and_lead(self, mock_post):
        mock_post.return_value = fake_response(201)

        send_message_via_brevo(self.message)

        self.message.refresh_from_db()
        self.lead.refresh_from_db()
        self.assertEqual(self.message.status, 'SENT')
        self.assertIsNotNone(self.message.sent_at)
        self.assertEqual(self.lead.status, 'CONTACTED')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_SENT', lead=self.lead).exists())

    @patch('prospects.services.email_sender.requests.post')
    def test_unsubscribe_link_included_in_body(self, mock_post):
        mock_post.return_value = fake_response(201)

        send_message_via_brevo(self.message)

        sent_payload = mock_post.call_args.kwargs['json']
        self.assertIn(f"/api/unsubscribe/{self.lead.id}/", sent_payload['textContent'])

    @patch('prospects.services.email_sender.requests.post')
    def test_unsubscribed_lead_blocks_send_without_api_call(self, mock_post):
        self.lead.unsubscribed = True
        self.lead.save(update_fields=['unsubscribed'])

        send_message_via_brevo(self.message)

        mock_post.assert_not_called()
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, 'FAILED')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_SEND_SKIPPED').exists())

    @patch('prospects.services.email_sender.requests.post')
    def test_brevo_error_marks_message_failed_and_raises(self, mock_post):
        mock_post.return_value = fake_response(401, text='{"code":"unauthorized"}')

        with self.assertRaises(requests.HTTPError):
            send_message_via_brevo(self.message)

        self.message.refresh_from_db()
        self.assertEqual(self.message.status, 'FAILED')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_SEND_FAILED').exists())

    @override_settings(BREVO_API_KEY='')
    @patch('prospects.services.email_sender.requests.post')
    def test_missing_config_raises_without_calling_api(self, mock_post):
        with self.assertRaises(ValueError):
            send_message_via_brevo(self.message)

        mock_post.assert_not_called()
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, 'FAILED')
