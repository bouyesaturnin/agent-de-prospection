from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from prospects.services.followup_manager import process_followups
from .factories import make_campaign, make_lead, make_message


class ProcessFollowupsTests(TestCase):
    def setUp(self):
        self.campaign = make_campaign(status='ACTIVE', followup_delay_days=3, max_followups=2)

    def _eligible_lead(self, **overrides):
        lead = make_lead(campaign=self.campaign, status='CONTACTED', **overrides)
        make_message(
            lead,
            status='SENT',
            sent_at=timezone.now() - timedelta(days=5),  # au-delà du délai de 3 jours
        )
        return lead

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_eligible_lead_generates_followup(self, mock_generate):
        lead = self._eligible_lead(email='eligible@example.com')

        result = process_followups()

        self.assertEqual(result['created'], 1)
        mock_generate.assert_called_once()
        called_lead = mock_generate.call_args.args[0]
        self.assertEqual(called_lead.id, lead.id)

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_inactive_campaign_is_skipped(self, mock_generate):
        self.campaign.status = 'PAUSED'
        self.campaign.save()
        self._eligible_lead(email='paused@example.com')

        result = process_followups()

        self.assertEqual(result['created'], 0)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_not_yet_due_is_skipped(self, mock_generate):
        lead = make_lead(campaign=self.campaign, status='CONTACTED', email='recent@example.com')
        make_message(lead, status='SENT', sent_at=timezone.now() - timedelta(hours=1))

        result = process_followups()

        self.assertEqual(result['created'], 0)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_lead_without_sent_message_is_skipped(self, mock_generate):
        make_lead(campaign=self.campaign, status='CONTACTED', email='nosent@example.com')

        result = process_followups()

        self.assertEqual(result['created'], 0)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_unsubscribed_lead_is_skipped(self, mock_generate):
        self._eligible_lead(email='unsub@example.com', unsubscribed=True)

        result = process_followups()

        self.assertEqual(result['created'], 0)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_pending_draft_blocks_new_followup(self, mock_generate):
        lead = self._eligible_lead(email='pending@example.com')
        make_message(lead, status='DRAFT')

        result = process_followups()

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped'], 1)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_max_followups_cap_respected(self, mock_generate):
        lead = self._eligible_lead(email='capped@example.com')  # 1 message SENT déjà
        # Ajoute 2 relances déjà envoyées => 3 messages SENT au total, max_followups=2 atteint
        make_message(lead, status='SENT', sent_at=timezone.now() - timedelta(days=4))
        make_message(lead, status='SENT', sent_at=timezone.now() - timedelta(days=4))

        result = process_followups()

        self.assertEqual(result['created'], 0)
        mock_generate.assert_not_called()

    @patch('prospects.services.followup_manager.generate_followup_email_with_claude')
    def test_generation_error_is_caught_and_counted_as_skipped(self, mock_generate):
        mock_generate.side_effect = RuntimeError("Claude indisponible")
        self._eligible_lead(email='error@example.com')

        result = process_followups()

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped'], 1)
