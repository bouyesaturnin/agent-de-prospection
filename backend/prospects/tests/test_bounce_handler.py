from django.test import TestCase

from prospects.models import AgentLog
from prospects.services.bounce_handler import process_bounce_event
from .factories import make_lead, make_message


class ProcessBounceEventTests(TestCase):
    def setUp(self):
        self.lead = make_lead(email='dest@example.com', status='CONTACTED')
        self.message = make_message(
            self.lead, status='SENT', brevo_message_id='<abc123@smtp-relay.mailin.fr>'
        )

    def test_hard_bounce_matched_by_message_id_marks_lead_and_message(self):
        result = process_bounce_event({
            'event': 'hard_bounce',
            'email': 'dest@example.com',
            'message-id': '<abc123@smtp-relay.mailin.fr>',
            'reason': 'Mailbox does not exist',
        })

        self.assertEqual(result, 'hard_bounce')
        self.message.refresh_from_db()
        self.lead.refresh_from_db()
        self.assertEqual(self.message.status, 'BOUNCED')
        self.assertEqual(self.lead.status, 'BOUNCED')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_BOUNCED', lead=self.lead).exists())

    def test_invalid_email_matched_by_recipient_when_no_message_id(self):
        result = process_bounce_event({'event': 'invalid_email', 'email': 'dest@example.com'})

        self.assertEqual(result, 'hard_bounce')
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, 'BOUNCED')

    def test_spam_complaint_unsubscribes_lead(self):
        result = process_bounce_event({
            'event': 'spam',
            'email': 'dest@example.com',
            'message-id': '<abc123@smtp-relay.mailin.fr>',
        })

        self.assertEqual(result, 'complaint')
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.unsubscribed)
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_COMPLAINT', lead=self.lead).exists())

    def test_soft_bounce_logs_without_changing_status(self):
        result = process_bounce_event({
            'event': 'soft_bounce',
            'email': 'dest@example.com',
            'message-id': '<abc123@smtp-relay.mailin.fr>',
        })

        self.assertEqual(result, 'soft_bounce')
        self.message.refresh_from_db()
        self.lead.refresh_from_db()
        self.assertEqual(self.message.status, 'SENT')
        self.assertEqual(self.lead.status, 'CONTACTED')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_SOFT_BOUNCE').exists())

    def test_unrelated_event_is_ignored(self):
        result = process_bounce_event({'event': 'opened', 'email': 'dest@example.com'})
        self.assertEqual(result, 'ignored')

    def test_unmatched_recipient_still_logs_without_crashing(self):
        result = process_bounce_event({'event': 'hard_bounce', 'email': 'unknown@example.com'})
        self.assertEqual(result, 'hard_bounce')
        self.assertTrue(AgentLog.objects.filter(action='EMAIL_BOUNCED', lead__isnull=True).exists())
