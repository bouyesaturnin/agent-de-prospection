import os
import json
import anthropic
from prospects.models import Lead, Campaign, Message, AgentLog


def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("La variable ANTHROPIC_API_KEY est manquante dans votre .env")
    return anthropic.Anthropic(api_key=api_key)


def _extract_json_response(response) -> dict:
    """
    Extrait et parse le JSON renvoyé par Claude. Le modèle peut renvoyer un bloc
    de réflexion ("thinking") avant le texte (content[0] n'est donc pas fiable),
    et enveloppe parfois sa réponse dans des balises markdown ```json.
    """
    raw_text = next((block.text for block in response.content if block.type == "text"), "")
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.removeprefix("json").strip()
    return json.loads(raw_text)


def generate_personalized_email_with_claude(lead: Lead, campaign: Campaign = None) -> Message:
    client = get_anthropic_client()

    system_prompt = (
        "Tu es un expert en prospection B2B et Copywriting commercial. "
        "Ton objectif est de rédiger un email d'accroche court, percutant, empathique et hautement personnalisé. "
        "Format de réponse attendu : un objet JSON strict avec deux clés : 'subject' et 'body'."
    )

    campaign_context = ""
    if campaign and campaign.ai_prompt_template:
        campaign_context = f"Instructions spécifiques à la campagne :\n{campaign.ai_prompt_template}\n\n"

    user_prompt = f"""
{campaign_context}Informations sur le prospect à contacter :
- Prénom : {lead.first_name or 'Non précisé'}
- Nom : {lead.last_name or 'Non précisé'}
- Entreprise : {lead.company or 'Non précisée'}
- Poste / Titre : {lead.job_title or 'Non précisé'}
- Site Web : {lead.website or 'Non précisé'}
- Notes / Enrichissement : {lead.notes or 'Aucune note particulière'}

Réponds STRICTEMENT au format JSON avec les clés "subject" et "body".
"""

    try:
        # Appel de l'API Claude (Sonnet pour la meilleure qualité de copywriting)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        result = _extract_json_response(response)

        subject = result.get("subject", f"Prise de contact - {lead.company}")
        body = result.get("body", "")

        # Création du message en base
        message = Message.objects.create(
            lead=lead,
            msg_type='EMAIL',
            status='DRAFT',
            subject=subject,
            body=body,
            generated_by_ai=True
        )

        lead.status = 'GENERATED'
        lead.save()

        AgentLog.objects.create(
            action='AI_MESSAGE_GENERATED_CLAUDE',
            level='INFO',
            message=f"Email généré via Claude pour {lead.email}",
            lead=lead,
            campaign=campaign
        )

        return message

    except Exception as e:
        AgentLog.objects.create(
            action='AI_GENERATION_FAILED',
            level='ERROR',
            message=f"Échec génération Claude pour {lead.email} : {str(e)}",
            lead=lead,
            campaign=campaign
        )
        raise e


def generate_followup_email_with_claude(lead: Lead, campaign: Campaign, previous_message: Message) -> Message:
    """
    Génère une relance (en brouillon) suite à un précédent email resté sans réponse.
    Ne modifie jamais le statut du lead ni n'envoie rien : la relance attend une
    validation manuelle avant envoi, comme n'importe quel autre message généré.
    """
    client = get_anthropic_client()

    system_prompt = (
        "Tu es un expert en prospection B2B et copywriting commercial. "
        "Tu rédiges une RELANCE suite à un premier email resté sans réponse. "
        "La relance doit être courte (3 à 4 phrases maximum), cordiale, apporter un angle "
        "légèrement différent du premier message (ne jamais le répéter mot pour mot), "
        "et ne jamais culpabiliser ou mettre la pression sur le prospect. "
        "Format de réponse attendu : un objet JSON strict avec deux clés : 'subject' et 'body'."
    )

    campaign_context = ""
    if campaign and campaign.ai_prompt_template:
        campaign_context = f"Instructions spécifiques à la campagne :\n{campaign.ai_prompt_template}\n\n"

    user_prompt = f"""
{campaign_context}Informations sur le prospect :
- Prénom : {lead.first_name or 'Non précisé'}
- Nom : {lead.last_name or 'Non précisé'}
- Entreprise : {lead.company or 'Non précisée'}
- Poste / Titre : {lead.job_title or 'Non précisé'}

Premier email envoyé (resté sans réponse à ce jour) :
Objet : {previous_message.subject}
{previous_message.body}

Rédige une relance courte suite à cet email.
Réponds STRICTEMENT au format JSON avec les clés "subject" et "body".
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=400,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        result = _extract_json_response(response)

        subject = result.get("subject", f"Relance - {previous_message.subject}")
        body = result.get("body", "")

        message = Message.objects.create(
            lead=lead,
            msg_type='EMAIL',
            status='DRAFT',
            subject=subject,
            body=body,
            generated_by_ai=True
        )

        AgentLog.objects.create(
            action='FOLLOWUP_GENERATED',
            level='INFO',
            message=f"Relance générée pour {lead.email} (brouillon en attente de validation).",
            lead=lead,
            campaign=campaign
        )

        return message

    except Exception as e:
        AgentLog.objects.create(
            action='FOLLOWUP_GENERATION_FAILED',
            level='ERROR',
            message=f"Échec génération relance pour {lead.email} : {str(e)}",
            lead=lead,
            campaign=campaign
        )
        raise e
