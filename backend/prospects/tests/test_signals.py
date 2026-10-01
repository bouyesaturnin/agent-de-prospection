from unittest.mock import patch

from django.test import TestCase

from prospects.models import AgentLog
from .factories import make_lead


class AlertOnErrorLogSignalTests(TestCase):
    @patch('prospects.signals.send_alert_email')
    def test_error_level_log_triggers_alert(self, mock_send_alert):
        lead = make_lead(email='dest@example.com')
        AgentLog.objects.create(action='EMAIL_SEND_FAILED', level='ERROR', message='Panne', lead=lead)

        mock_send_alert.assert_called_once()
        subject, body = mock_send_alert.call_args.args
        self.assertIn('EMAIL_SEND_FAILED', subject)
        self.assertIn('Panne', body)
        self.assertIn('dest@example.com', body)

    @patch('prospects.signals.send_alert_email')
    def test_info_level_log_does_not_trigger_alert(self, mock_send_alert):
        AgentLog.objects.create(action='EMAIL_SENT', level='INFO', message='Tout va bien')
        mock_send_alert.assert_not_called()

    @patch('prospects.signals.send_alert_email')
    def test_warning_level_log_does_not_trigger_alert(self, mock_send_alert):
        AgentLog.objects.create(action='EMAIL_BOUNCED', level='WARNING', message='Bounce')
        mock_send_alert.assert_not_called()

    @patch('prospects.signals.send_alert_email')
    def test_updating_existing_log_does_not_retrigger_alert(self, mock_send_alert):
        log = AgentLog.objects.create(action='EMAIL_SEND_FAILED', level='ERROR', message='Panne')
        mock_send_alert.reset_mock()

        log.message = 'Panne (mise à jour)'
        log.save(update_fields=['message'])

        mock_send_alert.assert_not_called()

    @patch('prospects.signals.send_alert_email')
    def test_error_log_without_lead_or_campaign_does_not_crash(self, mock_send_alert):
        AgentLog.objects.create(action='EMAIL_SEND_FAILED', level='ERROR', message='Panne orpheline')
        mock_send_alert.assert_called_once()
