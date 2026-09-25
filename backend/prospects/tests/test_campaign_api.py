from rest_framework import status

from prospects.models import AgentLog, Campaign
from .base import AuthenticatedAPITestCase
from .factories import make_campaign, make_lead


class CampaignApiTests(AuthenticatedAPITestCase):
    def test_create_campaign(self):
        response = self.client.post('/api/campaigns/', {'name': 'Prospection Q4', 'status': 'DRAFT'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.get().name, 'Prospection Q4')
        # Valeurs par défaut des relances
        self.assertEqual(response.data['followup_delay_days'], 3)
        self.assertEqual(response.data['max_followups'], 2)

    def test_leads_count_annotation(self):
        campaign = make_campaign()
        make_lead(email='a@example.com', campaign=campaign)
        make_lead(email='b@example.com', campaign=campaign)

        response = self.client.get(f'/api/campaigns/{campaign.id}/')
        self.assertEqual(response.data['leads_count'], 2)

    def test_start_campaign_action(self):
        campaign = make_campaign(status='DRAFT')
        response = self.client.post(f'/api/campaigns/{campaign.id}/start/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        campaign.refresh_from_db()
        self.assertEqual(campaign.status, 'ACTIVE')
        self.assertTrue(AgentLog.objects.filter(action='CAMPAIGN_STARTED', campaign=campaign).exists())

    def test_pause_campaign_action(self):
        campaign = make_campaign(status='ACTIVE')
        response = self.client.post(f'/api/campaigns/{campaign.id}/pause/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        campaign.refresh_from_db()
        self.assertEqual(campaign.status, 'PAUSED')

    def test_delete_campaign(self):
        campaign = make_campaign()
        response = self.client.delete(f'/api/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Campaign.objects.filter(id=campaign.id).exists())

    def test_deleting_campaign_keeps_leads_unassigned(self):
        """Lead.campaign est SET_NULL : supprimer une campagne ne doit pas supprimer ses leads."""
        campaign = make_campaign()
        lead = make_lead(email='keep@example.com', campaign=campaign)

        self.client.delete(f'/api/campaigns/{campaign.id}/')

        lead.refresh_from_db()
        self.assertIsNone(lead.campaign)
