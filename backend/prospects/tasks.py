from celery import shared_task
from .models import Lead, Message
from .services.ai_agent import generate_personalized_email_with_claude
from .services.email_sender import send_message_via_brevo
from .services.reply_checker import check_replies
from .services.followup_manager import process_followups


@shared_task
def task_generate_ai_message(lead_id):
    """
    Tâche Celery exécutée en arrière-plan pour générer un message IA.
    """
    try:
        lead = Lead.objects.get(id=lead_id)
        message = generate_personalized_email_with_claude(lead, campaign=lead.campaign)
        return f"Message {message.id} généré avec succès pour {lead.email}"
    except Lead.DoesNotExist:
        return f"Lead avec ID {lead_id} introuvable."
    except Exception as e:
        return f"Erreur lors de la génération pour l'ID {lead_id}: {str(e)}"


@shared_task
def task_send_message(message_id):
    """
    Tâche Celery exécutée en arrière-plan pour envoyer un message par email via Brevo.
    """
    try:
        message = Message.objects.select_related('lead').get(id=message_id)
        send_message_via_brevo(message)
        return f"Message {message.id} envoyé avec succès à {message.lead.email}"
    except Message.DoesNotExist:
        return f"Message avec ID {message_id} introuvable."
    except Exception as e:
        return f"Erreur lors de l'envoi du message {message_id}: {str(e)}"


@shared_task
def task_check_replies():
    """
    Tâche Celery périodique (voir CELERY_BEAT_SCHEDULE) qui relève la boîte IMAP
    à la recherche de réponses de prospects.
    """
    try:
        result = check_replies()
        return f"{result['matched']} réponse(s) associée(s), {result['ignored']} email(s) ignoré(s)."
    except Exception as e:
        return f"Erreur lors du relevé des réponses : {str(e)}"


@shared_task
def task_process_followups():
    """
    Tâche Celery périodique qui génère des relances (en brouillon) pour les
    prospects contactés sans réponse depuis trop longtemps, selon la config de
    chaque campagne active. Ne fait jamais d'envoi automatique.
    """
    try:
        result = process_followups()
        return f"{result['created']} relance(s) générée(s), {result['skipped']} ignoré(s)."
    except Exception as e:
        return f"Erreur lors du traitement des relances : {str(e)}"