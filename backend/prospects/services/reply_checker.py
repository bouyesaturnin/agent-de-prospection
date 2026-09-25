import email
import imaplib
from email.header import decode_header
from email.utils import parseaddr

from django.conf import settings

from prospects.models import AgentLog, ImapSyncState, Lead, Message

MAX_MESSAGES_PER_RUN = 200


def _decode_header_value(value) -> str:
    if not value:
        return ''
    parts = decode_header(value)
    decoded = ''
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded += text.decode(charset or 'utf-8', errors='replace')
        else:
            decoded += text
    return decoded


def _extract_plain_text(msg) -> str:
    if not msg.is_multipart():
        charset = msg.get_content_charset() or 'utf-8'
        payload = msg.get_payload(decode=True)
        return payload.decode(charset, errors='replace') if payload else ''

    for part in msg.walk():
        disposition = str(part.get('Content-Disposition') or '')
        if part.get_content_type() == 'text/plain' and 'attachment' not in disposition:
            charset = part.get_content_charset() or 'utf-8'
            payload = part.get_payload(decode=True)
            return payload.decode(charset, errors='replace') if payload else ''

    # Repli : pas de texte brut trouvé, on prend le premier bloc HTML tel quel.
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            charset = part.get_content_charset() or 'utf-8'
            payload = part.get_payload(decode=True)
            return payload.decode(charset, errors='replace') if payload else ''

    return ''


def _highest_uid(conn) -> int:
    status, data = conn.uid('search', None, 'ALL')
    if status != 'OK' or not data or not data[0]:
        return 0
    uids = [int(x) for x in data[0].split()]
    return max(uids) if uids else 0


def check_replies() -> dict:
    """
    Se connecte à la boîte IMAP configurée et ne traite QUE les emails reçus depuis
    le dernier passage (suivi par UID en base, jamais par le flag \\Seen — une boîte
    personnelle peut contenir des dizaines de milliers d'emails non lus sans rapport).

    Au tout premier lancement, on n'analyse aucun historique : on mémorise juste le
    point de départ, pour ne surveiller que les emails à venir.

    La connexion est ouverte en lecture seule (readonly) et chaque message est
    récupéré via BODY.PEEK[], donc rien n'est jamais modifié dans la boîte mail
    (aucun message n'est marqué comme lu).

    Lève une exception si la configuration est incomplète ou la connexion échoue.
    """
    if not settings.IMAP_HOST or not settings.IMAP_USERNAME or not settings.IMAP_PASSWORD:
        raise ValueError("Configuration IMAP incomplète (IMAP_HOST / IMAP_USERNAME / IMAP_PASSWORD).")

    mailbox_key = f"{settings.IMAP_HOST}:{settings.IMAP_USERNAME}:{settings.IMAP_MAILBOX}"
    sync_state, created = ImapSyncState.objects.get_or_create(mailbox_key=mailbox_key)

    matched, ignored = 0, 0

    conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT, timeout=15)
    try:
        conn.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        conn.select(settings.IMAP_MAILBOX, readonly=True)

        if created:
            sync_state.last_uid = _highest_uid(conn)
            sync_state.save(update_fields=['last_uid'])
            return {'matched': 0, 'ignored': 0}

        status, data = conn.uid('search', None, f'{sync_state.last_uid + 1}:*')
        if status != 'OK' or not data or not data[0]:
            return {'matched': 0, 'ignored': 0}

        new_uids = sorted(u for u in (int(x) for x in data[0].split()) if u > sync_state.last_uid)
        batch = new_uids[:MAX_MESSAGES_PER_RUN]

        highest_processed = sync_state.last_uid
        for uid in batch:
            highest_processed = max(highest_processed, uid)

            status, msg_data = conn.uid('fetch', str(uid), '(BODY.PEEK[])')
            if status != 'OK' or not msg_data or not msg_data[0]:
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            _, sender_email = parseaddr(msg.get('From', ''))
            sender_email = sender_email.strip().lower()

            lead = Lead.objects.filter(email__iexact=sender_email).first() if sender_email else None
            if lead is None:
                ignored += 1
                continue

            Message.objects.create(
                lead=lead,
                msg_type='EMAIL',
                status='RECEIVED',
                subject=_decode_header_value(msg.get('Subject', '')),
                body=_extract_plain_text(msg).strip(),
                generated_by_ai=False,
            )

            if lead.status != 'UNQUALIFIED':
                lead.status = 'REPLIED'
                lead.save(update_fields=['status'])

            AgentLog.objects.create(
                action='REPLY_RECEIVED',
                level='INFO',
                message=f"Réponse reçue de {lead.email}.",
                lead=lead,
                campaign=lead.campaign,
            )
            matched += 1

        sync_state.last_uid = highest_processed
        sync_state.save(update_fields=['last_uid'])
    finally:
        conn.logout()

    return {'matched': matched, 'ignored': ignored}
