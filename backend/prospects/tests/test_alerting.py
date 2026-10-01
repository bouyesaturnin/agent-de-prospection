from unittest.mock import patch

from django.test import TestCase, override_settings

from prospects.services.alerting import send_alert_email


@override_settings(
    BREVO_API_KEY='test-key',
    BREVO_SENDER_EMAIL='sender@example.com',
    BREVO_SENDER_NAME='Test Sender',
    ADMIN_ALERT_EMAIL='admin@example.com',
)
class SendAlertEmailTests(TestCase):
    @patch('prospects.services.alerting.requests.post')
    def test_sends_alert_with_expected_payload(self, mock_post):
        send_alert_email('Panne test', 'Corps du message.')

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs['json']
        self.assertEqual(payload['to'], [{'email': 'admin@example.com'}])
        self.assertIn('Panne test', payload['subject'])
        self.assertEqual(payload['textContent'], 'Corps du message.')

    @patch('prospects.services.alerting.requests.post')
    def test_network_error_does_not_raise(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError('boom')

        send_alert_email('Panne test', 'Corps du message.')  # ne doit pas lever

    @override_settings(ADMIN_ALERT_EMAIL='')
    @patch('prospects.services.alerting.requests.post')
    def test_no_admin_email_configured_skips_without_calling_api(self, mock_post):
        send_alert_email('Panne test', 'Corps du message.')
        mock_post.assert_not_called()

    @override_settings(BREVO_API_KEY='')
    @patch('prospects.services.alerting.requests.post')
    def test_missing_brevo_key_skips_without_calling_api(self, mock_post):
        send_alert_email('Panne test', 'Corps du message.')
        mock_post.assert_not_called()
