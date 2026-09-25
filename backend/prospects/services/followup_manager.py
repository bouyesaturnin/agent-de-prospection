from datetime import timedelta

from django.utils import timezone

from prospects.models import Campaign, Lead
from prospects.services.ai_agent import generate_followup_email_with_claude


def process_followups() -> dict:
    """
    Parcourt les campagnes actives et génère une relance (brouillon) pour chaque
    prospect contacté sans réponse depuis plus de `followup_delay_days`, dans la
    limite de `max_followups` par prospect. Ne modifie jamais le statut du lead
    et n'envoie jamais rien automatiquement — chaque relance attend une validation
    manuelle avant envoi.
    """
    created, skipped = 0, 0

    for campaign in Campaign.objects.filter(status='ACTIVE'):
        cutoff = timezone.now() - timedelta(days=campaign.followup_delay_days)

        leads = Lead.objects.filter(
            campaign=campaign,
            status='CONTACTED',
            unsubscribed=False,
        )

        for lead in leads:
            # Ne jamais générer une nouvelle relance si un brouillon est déjà en attente
            if lead.messages.filter(status__in=['DRAFT', 'QUEUED']).exists():
                skipped += 1
                continue

            sent_messages = lead.messages.filter(msg_type='EMAIL', status='SENT').order_by('-sent_at')
            last_sent = sent_messages.first()
            if last_sent is None or last_sent.sent_at is None or last_sent.sent_at > cutoff:
                continue  # pas encore le moment, ou aucun email envoyé

            followups_already_sent = sent_messages.count() - 1  # le tout premier envoi ne compte pas
            if followups_already_sent >= campaign.max_followups:
                continue  # plafond de relances atteint pour ce prospect

            try:
                generate_followup_email_with_claude(lead, campaign, last_sent)
                created += 1
            except Exception:
                # déjà journalisé (AgentLog) par generate_followup_email_with_claude
                skipped += 1

    return {'created': created, 'skipped': skipped}
