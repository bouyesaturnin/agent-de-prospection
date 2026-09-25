from io import BytesIO
from unittest.mock import patch

from rest_framework import status

from prospects.models import Lead
from .base import AuthenticatedAPITestCase
from .factories import make_campaign, make_lead


class LeadCrudTests(AuthenticatedAPITestCase):
    def test_create_lead(self):
        response = self.client.post('/api/leads/', {'email': 'new@example.com', 'first_name': 'Ana'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.get().status, 'NEW')
        self.assertFalse(Lead.objects.get().unsubscribed)

    def test_duplicate_email_rejected(self):
        make_lead(email='dup@example.com')
        response = self.client.post('/api/leads/', {'email': 'dup@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_lead(self):
        lead = make_lead(email='update@example.com')
        response = self.client.patch(f'/api/leads/{lead.id}/', {'company': 'Acme'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lead.refresh_from_db()
        self.assertEqual(lead.company, 'Acme')

    def test_delete_lead(self):
        lead = make_lead(email='delete@example.com')
        response = self.client.delete(f'/api/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())

    def test_filter_leads_by_status(self):
        make_lead(email='new1@example.com', status='NEW')
        make_lead(email='contacted1@example.com', status='CONTACTED')

        response = self.client.get('/api/leads/', {'status': 'CONTACTED'})
        emails = [item['email'] for item in response.data['results']]
        self.assertEqual(emails, ['contacted1@example.com'])


class LeadImportCsvTests(AuthenticatedAPITestCase):
    def _upload(self, content: str, campaign_id=None):
        data = {'file': BytesIO(content.encode('utf-8'))}
        data['file'].name = 'leads.csv'
        if campaign_id:
            data['campaign'] = str(campaign_id)
        return self.client.post('/api/leads/import_csv/', data, format='multipart')

    def test_import_creates_leads_and_skips_duplicates(self):
        make_lead(email='existing@example.com')
        csv_content = (
            "email,first_name,last_name,company\n"
            "alice@example.com,Alice,Martin,Acme\n"
            "existing@example.com,Should,Skip,Dup\n"
        )
        response = self._upload(csv_content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['skipped'], 1)
        self.assertTrue(Lead.objects.filter(email='alice@example.com').exists())

    def test_import_assigns_campaign(self):
        campaign = make_campaign()
        response = self._upload("email\nassigned@example.com\n", campaign_id=campaign.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead = Lead.objects.get(email='assigned@example.com')
        self.assertEqual(lead.campaign_id, campaign.id)

    def test_import_missing_email_column_rejected(self):
        response = self._upload("first_name\nAlice\n")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_missing_file_rejected(self):
        response = self.client.post('/api/leads/import_csv/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LeadGenerateAiMessageTests(AuthenticatedAPITestCase):
    @patch('prospects.views.task_generate_ai_message')
    @patch('prospects.views._broker_reachable', return_value=True)
    def test_generate_ai_message_queues_task(self, mock_reachable, mock_task):
        lead = make_lead(email='ai@example.com')
        response = self.client.post(f'/api/leads/{lead.id}/generate_ai_message/')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.delay.assert_called_once_with(str(lead.id))

    @patch('prospects.views._broker_reachable', return_value=False)
    def test_generate_ai_message_returns_503_when_broker_down(self, mock_reachable):
        lead = make_lead(email='ai2@example.com')
        response = self.client.post(f'/api/leads/{lead.id}/generate_ai_message/')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class LeadCheckRepliesTests(AuthenticatedAPITestCase):
    @patch('prospects.views.check_replies', return_value={'matched': 2, 'ignored': 5})
    def test_check_replies_returns_result(self, mock_check):
        response = self.client.post('/api/leads/check_replies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'matched': 2, 'ignored': 5})

    @patch('prospects.views.check_replies', side_effect=ValueError("Configuration IMAP incomplète"))
    def test_check_replies_missing_config_returns_400(self, mock_check):
        response = self.client.post('/api/leads/check_replies/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('prospects.views.check_replies', side_effect=OSError("connection refused"))
    def test_check_replies_connection_error_returns_502(self, mock_check):
        response = self.client.post('/api/leads/check_replies/')
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class LeadProcessFollowupsTests(AuthenticatedAPITestCase):
    @patch('prospects.views.process_followups', return_value={'created': 1, 'skipped': 0})
    def test_process_followups_returns_result(self, mock_process):
        response = self.client.post('/api/leads/process_followups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'created': 1, 'skipped': 0})
