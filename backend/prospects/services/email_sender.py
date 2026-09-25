import requests
from django.conf import settings
from django.utils import timezone

from prospects.models import AgentLog, Message

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _unsubscribe_footer(lead) -> str:
    unsubscribe_url = f"{settings.PUBLIC_BACKEND_URL}/api/unsubscribe/{lead.id}/"
    return (
        "\n\n---\n"
        "Vous recevez cet email dans le cadre d'une démarche de prospection commerciale.\n"
        f"Pour ne plus recevoir de message de notre part : {unsubscribe_url}"
    )


def send_message_via_brevo(message: Message) -> None:
    """
    Envoie un Message par email via l'API Brevo et met à jour son statut.
    Lève une exception si l'envoi échoue (le statut est alors passé à FAILED avant).
    """
    lead = message.lead

    if lead.unsubscribed:
        message.status = 'FAILED'
        message.save(update_fields=['status'])
        AgentLog.objects.create(
            action='EMAIL_SEND_SKIPPED',
            level='WARNING',
            message=f"Envoi annulé : {lead.email} s'est désinscrit.",
            lead=lead,
            campaign=lead.campaign,
        )
        return

    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        message.status = 'FAILED'
        message.save(update_fields=['status'])
        AgentLog.objects.create(
            action='EMAIL_SEND_FAILED',
            level='ERROR',
            message="BREVO_API_KEY ou BREVO_SENDER_EMAIL manquant dans la configuration (.env).",
            lead=lead,
            campaign=lead.campaign,
        )
        raise ValueError("Configuration Brevo incomplète (BREVO_API_KEY / BREVO_SENDER_EMAIL).")

    recipient_name = f"{lead.first_name} {lead.last_name}".strip() or lead.email
    payload = {
        "sender": {"email": settings.BREVO_SENDER_EMAIL, "name": settings.BREVO_SENDER_NAME},
        "to": [{"email": lead.email, "name": recipient_name}],
        "subject": message.subject or "Prise de contact",
        "textContent": message.body + _unsubscribe_footer(lead),
    }

    response = requests.post(
        BREVO_API_URL,
        json=payload,
        headers={
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=15,
    )

    if response.status_code >= 300:
        message.status = 'FAILED'
        message.save(update_fields=['status'])
        AgentLog.objects.create(
            action='EMAIL_SEND_FAILED',
            level='ERROR',
            message=f"Échec envoi Brevo pour {lead.email} ({response.status_code}) : {response.text[:300]}",
            lead=lead,
            campaign=lead.campaign,
        )
        response.raise_for_status()

    message.status = 'SENT'
    message.sent_at = timezone.now()
    message.save(update_fields=['status', 'sent_at'])

    lead.status = 'CONTACTED'
    lead.save(update_fields=['status'])

    AgentLog.objects.create(
        action='EMAIL_SENT',
        level='INFO',
        message=f"Email envoyé à {lead.email} via Brevo.",
        lead=lead,
        campaign=lead.campaign,
    )
