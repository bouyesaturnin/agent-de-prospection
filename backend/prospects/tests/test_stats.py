from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from prospects.services.stats import compute_stats
from .base import AuthenticatedAPITestCase
from .factories import make_campaign, make_lead, make_message


class ComputeStatsTests(AuthenticatedAPITestCase):
    def test_empty_database_returns_zeros_and_null_rates(self):
        data = compute_stats()

        self.assertEqual(sum(data['funnel'].values()), 0)
        self.assertIsNone(data['rates']['reply_rate'])
        self.assertIsNone(data['rates']['qualification_rate'])
        self.assertIsNone(data['rates']['bounce_rate'])
        self.assertEqual(data['messages_per_day'], [])
        self.assertEqual(data['by_campaign'], [])

    def test_funnel_counts_leads_by_status(self):
        make_lead(status='NEW')
        make_lead(status='NEW')
        make_lead(status='CONTACTED')
        make_lead(status='REPLIED')
        make_lead(status='QUALIFIED')

        data = compute_stats()

        self.assertEqual(data['funnel']['NEW'], 2)
        self.assertEqual(data['funnel']['CONTACTED'], 1)
        self.assertEqual(data['funnel']['REPLIED'], 1)
        self.assertEqual(data['funnel']['QUALIFIED'], 1)
        self.assertEqual(data['funnel']['UNQUALIFIED'], 0)

    def test_reply_and_qualification_rates(self):
        make_lead(status='CONTACTED')
        make_lead(status='CONTACTED')
        make_lead(status='REPLIED')
        make_lead(status='QUALIFIED')

        data = compute_stats()

        # contacted_total = 2 CONTACTED + 1 REPLIED + 1 QUALIFIED = 4
        # replied_total = 1 REPLIED + 1 QUALIFIED = 2
        self.assertAlmostEqual(data['rates']['reply_rate'], 2 / 4)
        self.assertAlmostEqual(data['rates']['qualification_rate'], 1 / 2)

    def test_bounce_rate(self):
        make_lead(status='CONTACTED')
        make_lead(status='CONTACTED')
        make_lead(status='CONTACTED')
        make_lead(status='BOUNCED')

        data = compute_stats()

        # attempted_total = 3 contacted + 1 bounced = 4
        self.assertAlmostEqual(data['rates']['bounce_rate'], 1 / 4)

    def test_messages_per_day_counts_only_sent_within_window(self):
        lead = make_lead()
        now = timezone.now()
        make_message(lead, status='SENT', sent_at=now)
        make_message(lead, status='SENT', sent_at=now)
        make_message(lead, status='DRAFT')  # jamais envoyé, ignoré
        make_message(lead, status='SENT', sent_at=now - timedelta(days=40))  # hors fenêtre

        data = compute_stats()

        self.assertEqual(len(data['messages_per_day']), 1)
        self.assertEqual(data['messages_per_day'][0]['date'], now.date().isoformat())
        self.assertEqual(data['messages_per_day'][0]['sent'], 2)

    def test_by_campaign_breakdown(self):
        campaign = make_campaign(name='Sites web')
        make_lead(campaign=campaign, status='CONTACTED')
        make_lead(campaign=campaign, status='REPLIED')
        make_lead(campaign=campaign, status='QUALIFIED')
        make_lead(status='NEW')  # sans campagne, ne doit pas compter dedans

        data = compute_stats()

        self.assertEqual(len(data['by_campaign']), 1)
        row = data['by_campaign'][0]
        self.assertEqual(row['name'], 'Sites web')
        self.assertEqual(row['leads_count'], 3)
        self.assertEqual(row['contacted'], 3)
        self.assertEqual(row['replied'], 2)
        self.assertEqual(row['qualified'], 1)


class StatsViewTests(AuthenticatedAPITestCase):
    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_computed_stats(self):
        make_lead(status='QUALIFIED')

        response = self.client.get('/api/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['funnel']['QUALIFIED'], 1)
