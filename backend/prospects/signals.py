from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AgentLog
from .services.alerting import send_alert_email


@receiver(post_save, sender=AgentLog)
def alert_on_error_log(sender, instance, created, **kwargs):
    """
    Envoie une alerte email dès qu'un incident (niveau ERROR) est journalisé :
    échec d'envoi, bounce définitif, plainte spam, échec de génération IA...
    Saturnin est prévenu sans avoir à consulter les journaux manuellement.
    """
    if not created or instance.level != 'ERROR':
        return

    subject = f"Erreur : {instance.action}"
    body = (
        f"{instance.message}\n\n"
        f"Lead : {instance.lead.email if instance.lead_id else '-'}\n"
        f"Campagne : {instance.campaign.name if instance.campaign_id else '-'}\n"
        f"Horodatage : {instance.timestamp}\n"
    )
    send_alert_email(subject, body)
