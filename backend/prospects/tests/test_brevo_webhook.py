import json

from django.test import TestCase, override_settings

from .factories import make_lead, make_message


@override_settings(BREVO_WEBHOOK_SECRET='test-secret')
class BrevoWebhookViewTests(TestCase):
    def setUp(self):
        self.lead = make_lead(email='dest@example.com', status='CONTACTED')
        self.message = make_message(
            self.lead, status='SENT', brevo_message_id='<abc123@smtp-relay.mailin.fr>'
        )

    def test_wrong_secret_rejected(self):
        response = self.client.post(
            '/api/webhooks/brevo/wrong-secret/',
            data=json.dumps({'event': 'hard_bounce', 'email': 'dest@example.com'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, 'SENT')

    def test_missing_secret_config_rejects_even_matching_value(self):
        with override_settings(BREVO_WEBHOOK_SECRET=''):
            response = self.client.post(
                '/api/webhooks/brevo//',
                data=json.dumps({'event': 'hard_bounce'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 404)  # empty path segment doesn't match the URL pattern

    def test_valid_secret_processes_hard_bounce(self):
        response = self.client.post(
            '/api/webhooks/brevo/test-secret/',
            data=json.dumps({
                'event': 'hard_bounce',
                'email': 'dest@example.com',
                'message-id': '<abc123@smtp-relay.mailin.fr>',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'processed': ['hard_bounce']})

        self.message.refresh_from_db()
        self.lead.refresh_from_db()
        self.assertEqual(self.message.status, 'BOUNCED')
        self.assertEqual(self.lead.status, 'BOUNCED')

    def test_handles_batch_of_events(self):
        second_lead = make_lead(email='second@example.com', status='CONTACTED')
        make_message(second_lead, status='SENT', brevo_message_id='<def456@smtp-relay.mailin.fr>')

        response = self.client.post(
            '/api/webhooks/brevo/test-secret/',
            data=json.dumps([
                {'event': 'hard_bounce', 'email': 'dest@example.com', 'message-id': '<abc123@smtp-relay.mailin.fr>'},
                {'event': 'spam', 'email': 'second@example.com', 'message-id': '<def456@smtp-relay.mailin.fr>'},
            ]),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'processed': ['hard_bounce', 'complaint']})

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            '/api/webhooks/brevo/test-secret/',
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_get_not_allowed(self):
        response = self.client.get('/api/webhooks/brevo/test-secret/')
        self.assertEqual(response.status_code, 405)
