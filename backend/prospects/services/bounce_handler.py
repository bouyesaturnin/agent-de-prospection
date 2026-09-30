from prospects.models import AgentLog, Message

# Adresse définitivement invalide : plus jamais recontacter, marquer le lead en erreur.
HARD_BOUNCE_EVENTS = {'hard_bounce', 'invalid_email'}
# Problème temporaire (boîte pleine, serveur indisponible...) : on garde une trace mais
# on ne bloque pas de futurs envois, ça peut passer la prochaine fois.
SOFT_BOUNCE_EVENTS = {'soft_bounce', 'blocked', 'deferred', 'error'}
# Plainte spam : obligation RGPD/anti-spam de ne plus jamais recontacter.
COMPLAINT_EVENTS = {'spam'}


def _extract_message_id(payload: dict) -> str:
    for key in ('message-id', 'messageId', 'message_id'):
        value = payload.get(key)
        if value:
            return value
    return ''


def _find_message(payload: dict) -> Message | None:
    brevo_message_id = _extract_message_id(payload)
    if brevo_message_id:
        message = (
            Message.objects.filter(brevo_message_id=brevo_message_id)
            .select_related('lead')
            .first()
        )
        if message:
            return message

    email = (payload.get('email') or '').strip()
    if not email:
        return None
    return (
        Message.objects.filter(lead__email__iexact=email, status='SENT')
        .select_related('lead')
        .order_by('-sent_at')
        .first()
    )


def process_bounce_event(payload: dict) -> str:
    """
    Traite un événement webhook Brevo (bounce, plainte spam...) et met à jour le
    Message/Lead concerné. Retourne une courte description de l'action prise, pour
    la réponse HTTP et les logs.
    """
    event = (payload.get('event') or '').lower()
    email = payload.get('email') or 'inconnu'
    reason = payload.get('reason') or ''

    message = _find_message(payload)

    if event in HARD_BOUNCE_EVENTS:
        if message:
            message.status = 'BOUNCED'
            message.save(update_fields=['status'])
            lead = message.lead
            lead.status = 'BOUNCED'
            lead.save(update_fields=['status'])
        AgentLog.objects.create(
            action='EMAIL_BOUNCED',
            level='WARNING',
            message=f"Bounce définitif ({event}) pour {email}. {reason}".strip(),
            lead=message.lead if message else None,
            campaign=message.lead.campaign if message else None,
        )
        return 'hard_bounce'

    if event in COMPLAINT_EVENTS:
        if message:
            lead = message.lead
            lead.unsubscribed = True
            lead.save(update_fields=['unsubscribed'])
        AgentLog.objects.create(
            action='EMAIL_COMPLAINT',
            level='ERROR',
            message=f"Plainte spam de {email} : désinscription automatique et définitive.",
            lead=message.lead if message else None,
            campaign=message.lead.campaign if message else None,
        )
        return 'complaint'

    if event in SOFT_BOUNCE_EVENTS:
        AgentLog.objects.create(
            action='EMAIL_SOFT_BOUNCE',
            level='INFO',
            message=f"Incident temporaire ({event}) pour {email}. {reason}".strip(),
            lead=message.lead if message else None,
            campaign=message.lead.campaign if message else None,
        )
        return 'soft_bounce'

    return 'ignored'
