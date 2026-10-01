from unittest.mock import patch

from django.test import TestCase


class HealthViewTests(TestCase):
    @patch('prospects.views._broker_reachable', return_value=True)
    def test_healthy_when_db_and_broker_reachable(self, mock_broker):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': True, 'broker': True})

    @patch('prospects.views._broker_reachable', return_value=False)
    def test_degraded_when_broker_unreachable(self, mock_broker):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body['status'], 'degraded')
        self.assertFalse(body['broker'])

    def test_is_public_no_auth_required(self):
        response = self.client.get('/api/health/')
        self.assertIn(response.status_code, (200, 503))

    def test_post_not_allowed(self):
        response = self.client.post('/api/health/')
        self.assertEqual(response.status_code, 405)
