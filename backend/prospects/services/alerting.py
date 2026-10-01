import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_alert_email(subject: str, body: str) -> None:
    """
    Envoie une alerte par email à l'administrateur (Saturnin) via Brevo, en cas
    d'erreur détectée par l'agent. Ne lève jamais d'exception et ne crée jamais
    de AgentLog : une alerte qui échoue à s'envoyer ne doit pas elle-même
    déclencher une nouvelle alerte en boucle.
    """
    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL or not settings.ADMIN_ALERT_EMAIL:
        logger.warning("Alerte non envoyée (configuration incomplète) : %s", subject)
        return

    payload = {
        "sender": {"email": settings.BREVO_SENDER_EMAIL, "name": settings.BREVO_SENDER_NAME},
        "to": [{"email": settings.ADMIN_ALERT_EMAIL}],
        "subject": f"[ProspectAI] {subject}",
        "textContent": body,
    }

    try:
        requests.post(
            BREVO_API_URL,
            json=payload,
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Échec de l'envoi de l'alerte : %s", subject)
