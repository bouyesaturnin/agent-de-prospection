from unittest.mock import patch

from rest_framework import status

from .base import AuthenticatedAPITestCase
from .factories import make_lead, make_message


class MessageSendTests(AuthenticatedAPITestCase):
    @patch('prospects.views.task_send_message')
    @patch('prospects.views._broker_reachable', return_value=True)
    def test_send_draft_message_queues_task(self, mock_reachable, mock_task):
        lead = make_lead(email='send@example.com')
        message = make_message(lead, status='DRAFT')

        response = self.client.post(f'/api/messages/{message.id}/send/')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.delay.assert_called_once_with(str(message.id))
        message.refresh_from_db()
        self.assertEqual(message.status, 'QUEUED')

    def test_send_already_sent_message_rejected(self):
        lead = make_lead(email='alreadysent@example.com')
        message = make_message(lead, status='SENT')

        response = self.client.post(f'/api/messages/{message.id}/send/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_to_unsubscribed_lead_blocked(self):
        lead = make_lead(email='unsub@example.com', unsubscribed=True)
        message = make_message(lead, status='DRAFT')

        response = self.client.post(f'/api/messages/{message.id}/send/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        message.refresh_from_db()
        self.assertEqual(message.status, 'DRAFT')  # jamais mis en QUEUED

    @patch('prospects.views._broker_reachable', return_value=False)
    def test_send_returns_503_and_reverts_status_when_broker_down(self, mock_reachable):
        lead = make_lead(email='brokerdown@example.com')
        message = make_message(lead, status='DRAFT')

        response = self.client.post(f'/api/messages/{message.id}/send/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        message.refresh_from_db()
        self.assertEqual(message.status, 'FAILED')
