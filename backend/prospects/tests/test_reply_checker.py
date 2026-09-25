from email.message import EmailMessage
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from prospects.models import AgentLog, ImapSyncState, Message
from prospects.services.reply_checker import check_replies
from .factories import make_lead

IMAP_TEST_SETTINGS = dict(
    IMAP_HOST='imap.test.invalid',
    IMAP_PORT=993,
    IMAP_USERNAME='agent@test.invalid',
    IMAP_PASSWORD='dummy-password',
    IMAP_MAILBOX='INBOX',
)


def build_raw_email(sender: str, subject: str, body: str) -> bytes:
    msg = EmailMessage()
    msg['From'] = sender
    msg['Subject'] = subject
    msg.set_content(body)
    return msg.as_bytes()


def build_fake_conn(all_uids=b'', search_uids=b'', fetch_map=None):
    """
    fetch_map: dict {uid_bytes_str: raw_email_bytes} utilisé pour répondre à conn.uid('fetch', uid, ...)
    """
    fetch_map = fetch_map or {}
    conn = MagicMock()

    def uid_side_effect(command, arg1, arg2=None):
        if command == 'search' and arg2 == 'ALL':
            return ('OK', [all_uids])
        if command == 'search':
            return ('OK', [search_uids])
        if command == 'fetch':
            # Pour 'fetch', le 2e argument positionnel est l'UID (pas None comme pour 'search')
            raw = fetch_map.get(arg1)
            if raw is None:
                return ('OK', [None])
            return ('OK', [(b'1 (UID %s BODY[] {%d}' % (arg1.encode(), len(raw)), raw)])
        raise AssertionError(f"commande IMAP inattendue : {command} {arg1} {arg2}")

    conn.uid.side_effect = uid_side_effect
    return conn


@override_settings(**IMAP_TEST_SETTINGS)
class CheckRepliesTests(TestCase):
    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_first_run_establishes_baseline_without_processing(self, mock_imap_ssl):
        conn = build_fake_conn(all_uids=b'1 2 3 10')
        mock_imap_ssl.return_value = conn

        result = check_replies()

        self.assertEqual(result, {'matched': 0, 'ignored': 0})
        conn.uid.assert_any_call('search', None, 'ALL')
        # Aucun fetch ne doit avoir lieu au tout premier passage (pas d'historique traité)
        fetch_calls = [c for c in conn.uid.call_args_list if c.args[0] == 'fetch']
        self.assertEqual(fetch_calls, [])

        state = ImapSyncState.objects.get(mailbox_key__contains='imap.test.invalid')
        self.assertEqual(state.last_uid, 10)

    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_connection_is_readonly(self, mock_imap_ssl):
        conn = build_fake_conn(all_uids=b'1')
        mock_imap_ssl.return_value = conn
        check_replies()
        conn.select.assert_called_once_with('INBOX', readonly=True)

    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_matches_known_lead_and_marks_replied(self, mock_imap_ssl):
        lead = make_lead(email='prospect@example.com', status='CONTACTED')
        mailbox_key = f"{IMAP_TEST_SETTINGS['IMAP_HOST']}:{IMAP_TEST_SETTINGS['IMAP_USERNAME']}:{IMAP_TEST_SETTINGS['IMAP_MAILBOX']}"
        ImapSyncState.objects.create(mailbox_key=mailbox_key, last_uid=10)

        raw = build_raw_email('prospect@example.com', 'Re: notre echange', 'Je suis interesse, merci !')
        conn = build_fake_conn(search_uids=b'11', fetch_map={'11': raw})
        mock_imap_ssl.return_value = conn

        result = check_replies()

        self.assertEqual(result, {'matched': 1, 'ignored': 0})

        lead.refresh_from_db()
        self.assertEqual(lead.status, 'REPLIED')

        message = Message.objects.get(lead=lead)
        self.assertEqual(message.status, 'RECEIVED')
        self.assertFalse(message.generated_by_ai)
        self.assertIn('interesse', message.body)

        self.assertTrue(AgentLog.objects.filter(action='REPLY_RECEIVED', lead=lead).exists())

        state = ImapSyncState.objects.get(mailbox_key=mailbox_key)
        self.assertEqual(state.last_uid, 11)

    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_uses_body_peek_never_marks_as_seen(self, mock_imap_ssl):
        """Vérifie qu'on utilise BODY.PEEK[] (jamais RFC822), pour ne jamais modifier le \\Seen du message."""
        make_lead(email='peek@example.com')
        mailbox_key = f"{IMAP_TEST_SETTINGS['IMAP_HOST']}:{IMAP_TEST_SETTINGS['IMAP_USERNAME']}:{IMAP_TEST_SETTINGS['IMAP_MAILBOX']}"
        ImapSyncState.objects.create(mailbox_key=mailbox_key, last_uid=0)

        raw = build_raw_email('peek@example.com', 'Sujet', 'Corps')
        conn = build_fake_conn(search_uids=b'1', fetch_map={'1': raw})
        mock_imap_ssl.return_value = conn

        check_replies()

        fetch_call = next(c for c in conn.uid.call_args_list if c.args[0] == 'fetch')
        self.assertEqual(fetch_call.args[2], '(BODY.PEEK[])')

    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_unknown_sender_is_ignored(self, mock_imap_ssl):
        mailbox_key = f"{IMAP_TEST_SETTINGS['IMAP_HOST']}:{IMAP_TEST_SETTINGS['IMAP_USERNAME']}:{IMAP_TEST_SETTINGS['IMAP_MAILBOX']}"
        ImapSyncState.objects.create(mailbox_key=mailbox_key, last_uid=0)

        raw = build_raw_email('inconnu@example.com', 'Sujet', 'Corps')
        conn = build_fake_conn(search_uids=b'1', fetch_map={'1': raw})
        mock_imap_ssl.return_value = conn

        result = check_replies()

        self.assertEqual(result, {'matched': 0, 'ignored': 1})
        self.assertFalse(Message.objects.exists())

    @override_settings(IMAP_HOST='', IMAP_USERNAME='', IMAP_PASSWORD='')
    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_missing_config_raises_without_connecting(self, mock_imap_ssl):
        with self.assertRaises(ValueError):
            check_replies()
        mock_imap_ssl.assert_not_called()

    @patch('prospects.services.reply_checker.imaplib.IMAP4_SSL')
    def test_unqualified_lead_status_not_overwritten(self, mock_imap_ssl):
        lead = make_lead(email='unqualified@example.com', status='UNQUALIFIED')
        mailbox_key = f"{IMAP_TEST_SETTINGS['IMAP_HOST']}:{IMAP_TEST_SETTINGS['IMAP_USERNAME']}:{IMAP_TEST_SETTINGS['IMAP_MAILBOX']}"
        ImapSyncState.objects.create(mailbox_key=mailbox_key, last_uid=0)

        raw = build_raw_email('unqualified@example.com', 'Sujet', 'Corps')
        conn = build_fake_conn(search_uids=b'1', fetch_map={'1': raw})
        mock_imap_ssl.return_value = conn

        check_replies()

        lead.refresh_from_db()
        self.assertEqual(lead.status, 'UNQUALIFIED')  # jamais rétrogradé automatiquement
