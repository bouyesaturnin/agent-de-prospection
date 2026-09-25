import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from prospects.models import AgentLog
from prospects.services.ai_agent import (
    generate_followup_email_with_claude,
    generate_personalized_email_with_claude,
)
from .factories import make_campaign, make_lead, make_message


def fake_claude_response(payload: dict, wrap_in_markdown=False, include_thinking_block=False):
    """Construit un faux objet réponse Anthropic, imitant sa forme réelle."""
    text = json.dumps(payload)
    if wrap_in_markdown:
        text = f"```json\n{text}\n```"

    blocks = []
    if include_thinking_block:
        blocks.append(SimpleNamespace(type='thinking', text=None))
    blocks.append(SimpleNamespace(type='text', text=text))
    return SimpleNamespace(content=blocks)


class GeneratePersonalizedEmailTests(TestCase):
    def setUp(self):
        self.lead = make_lead(email='prospect@example.com', first_name='Marie', company='Acme')
        self.campaign = make_campaign()

    @patch('prospects.services.ai_agent.get_anthropic_client')
    def test_successful_generation_creates_draft_message(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_claude_response(
            {'subject': 'Bonjour Marie', 'body': 'Contenu du message.'}
        )
        mock_get_client.return_value = mock_client

        message = generate_personalized_email_with_claude(self.lead, campaign=self.campaign)

        self.assertEqual(message.subject, 'Bonjour Marie')
        self.assertEqual(message.status, 'DRAFT')
        self.assertTrue(message.generated_by_ai)

        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'GENERATED')
        self.assertTrue(AgentLog.objects.filter(action='AI_MESSAGE_GENERATED_CLAUDE', lead=self.lead).exists())

    @patch('prospects.services.ai_agent.get_anthropic_client')
    def test_handles_markdown_wrapped_json(self, mock_get_client):
        """Claude enveloppe parfois sa réponse dans ```json ... ``` : doit être nettoyé avant parsing."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_claude_response(
            {'subject': 'Sujet', 'body': 'Corps'}, wrap_in_markdown=True
        )
        mock_get_client.return_value = mock_client

        message = generate_personalized_email_with_claude(self.lead)
        self.assertEqual(message.subject, 'Sujet')

    @patch('prospects.services.ai_agent.get_anthropic_client')
    def test_handles_leading_thinking_block(self, mock_get_client):
        """content[0] peut être un bloc 'thinking' : le texte doit être retrouvé quelle que soit sa position."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_claude_response(
            {'subject': 'Sujet', 'body': 'Corps'}, include_thinking_block=True
        )
        mock_get_client.return_value = mock_client

        message = generate_personalized_email_with_claude(self.lead)
        self.assertEqual(message.subject, 'Sujet')

    @patch('prospects.services.ai_agent.get_anthropic_client')
    def test_api_failure_logs_error_and_reraises(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API indisponible")
        mock_get_client.return_value = mock_client

        with self.assertRaises(RuntimeError):
            generate_personalized_email_with_claude(self.lead)

        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'NEW')  # inchangé
        self.assertTrue(AgentLog.objects.filter(action='AI_GENERATION_FAILED', lead=self.lead).exists())


class GenerateFollowupEmailTests(TestCase):
    def setUp(self):
        self.campaign = make_campaign()
        self.lead = make_lead(email='followup@example.com', campaign=self.campaign, status='CONTACTED')
        self.previous_message = make_message(self.lead, status='SENT', subject='Premier email', body='Corps initial')

    @patch('prospects.services.ai_agent.get_anthropic_client')
    def test_followup_creates_draft_without_changing_lead_status(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = fake_claude_response(
            {'subject': 'Petite relance', 'body': 'Contenu de la relance.'}
        )
        mock_get_client.return_value = mock_client

        message = generate_followup_email_with_claude(self.lead, self.campaign, self.previous_message)

        self.assertEqual(message.status, 'DRAFT')
        self.assertEqual(message.subject, 'Petite relance')

        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'CONTACTED')  # jamais modifié par une relance
        self.assertTrue(AgentLog.objects.filter(action='FOLLOWUP_GENERATED', lead=self.lead).exists())
