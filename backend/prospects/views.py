import csv
import io
import socket
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from kombu.exceptions import OperationalError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Campaign, Lead, Message, AgentLog
from .serializers import (
    CampaignSerializer,
    LeadSerializer,
    MessageSerializer,
    AgentLogSerializer,
)
from .services.reply_checker import check_replies
from .services.followup_manager import process_followups
from .tasks import task_generate_ai_message, task_send_message


def _broker_reachable(timeout=1.5) -> bool:
    """
    Vérifie que le broker Celery (Redis) accepte une connexion TCP, avec un
    délai borné. Nécessaire car sur certaines machines Windows, la résolution
    de 'localhost' essaie d'abord IPv6 puis IPv4, ce qui ralentit (et Celery/
    kombu peuvent retenter la connexion en interne bien plus longtemps encore).
    """
    parsed = urlparse(settings.CELERY_BROKER_URL)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 6379
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _delay_or_503(task, *args):
    """
    Enfile une tâche Celery. Si le broker (Redis) est injoignable, on préfère
    échouer immédiatement avec un message clair plutôt que de laisser la
    requête HTTP du client attendre pendant que Celery retente la connexion.
    """
    if not _broker_reachable():
        return Response(
            {
                'detail': "Le service de traitement en arrière-plan (Redis/Celery) est "
                          "indisponible. Vérifie qu'ils sont bien démarrés."
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        task.delay(*args)
    except OperationalError:
        return Response(
            {
                'detail': "Le service de traitement en arrière-plan (Redis/Celery) est "
                          "indisponible. Vérifie qu'ils sont bien démarrés."
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return None


class CampaignViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les campagnes de prospection.
    """
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Action personnalisée pour démarrer la campagne."""
        campaign = self.get_object()
        campaign.status = 'ACTIVE'
        campaign.save()

        AgentLog.objects.create(
            action='CAMPAIGN_STARTED',
            level='INFO',
            message=f"La campagne '{campaign.name}' a été démarrée.",
            campaign=campaign
        )
        return Response({'status': 'Campagne démarrée avec succès'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Action personnalisée pour mettre en pause la campagne."""
        campaign = self.get_object()
        campaign.status = 'PAUSED'
        campaign.save()
        return Response({'status': 'Campagne mise en pause'}, status=status.HTTP_200_OK)


class LeadViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les prospects.
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filterset_fields = ['status', 'campaign']

    @action(detail=True, methods=['post'])
    def generate_ai_message(self, request, pk=None):
        """
        Déclenche la génération d'un message IA en arrière-plan via Celery.
        """
        lead = self.get_object()

        # Lancement de la tâche asynchrone (retourne immédiatement)
        error = _delay_or_503(task_generate_ai_message, str(lead.id))
        if error:
            return error

        return Response(
            {
                "status": "Génération en cours en arrière-plan",
                "lead_id": str(lead.id)
            },
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        """
        Importe des prospects en masse depuis un fichier CSV.
        Colonnes attendues (en-tête insensible à la casse) : email (obligatoire),
        first_name, last_name, phone, company, job_title, linkedin_url, website, notes.
        Les emails déjà présents en base sont ignorés (pas de doublon).
        """
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': "Aucun fichier fourni (champ 'file' attendu)."}, status=400)

        campaign = None
        campaign_id = request.data.get('campaign')
        if campaign_id:
            campaign = Campaign.objects.filter(id=campaign_id).first()
            if campaign is None:
                return Response({'detail': "Campagne introuvable."}, status=400)

        try:
            decoded = uploaded_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response({'detail': "Encodage non supporté, utilisez un fichier CSV en UTF-8."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        fieldnames = {(f or '').strip().lower() for f in (reader.fieldnames or [])}
        if 'email' not in fieldnames:
            return Response({'detail': "Le fichier CSV doit contenir au minimum une colonne 'email'."}, status=400)

        created, skipped, errors = 0, 0, []
        for line_number, raw_row in enumerate(reader, start=2):
            row = {(k or '').strip().lower(): (v or '').strip() for k, v in raw_row.items()}
            email = row.get('email')
            if not email:
                errors.append(f"Ligne {line_number} : email manquant.")
                continue
            if Lead.objects.filter(email=email).exists():
                skipped += 1
                continue
            try:
                Lead.objects.create(
                    email=email,
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    phone=row.get('phone', ''),
                    company=row.get('company', ''),
                    job_title=row.get('job_title', ''),
                    linkedin_url=row.get('linkedin_url', ''),
                    website=row.get('website', ''),
                    notes=row.get('notes', ''),
                    campaign=campaign,
                )
                created += 1
            except Exception as exc:
                errors.append(f"Ligne {line_number} : {exc}")

        AgentLog.objects.create(
            action='LEADS_IMPORTED',
            level='INFO' if not errors else 'WARNING',
            message=f"{created} prospect(s) importé(s), {skipped} doublon(s) ignoré(s), {len(errors)} erreur(s).",
            campaign=campaign,
        )

        return Response(
            {'created': created, 'skipped': skipped, 'errors': errors},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def check_replies(self, request):
        """
        Relève immédiatement la boîte IMAP à la recherche de réponses de prospects
        (exécution synchrone : utile pour un bouton "Vérifier maintenant" côté UI).
        """
        try:
            result = check_replies()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # imaplib lève des IMAP4.error / OSError variés selon le cas
            return Response(
                {'detail': f"Impossible de relever la boîte mail : {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def process_followups(self, request):
        """
        Génère immédiatement les relances éligibles (brouillons, jamais envoyées
        automatiquement) pour les campagnes actives — exécution synchrone, utile
        pour un bouton "Générer les relances" côté UI.
        """
        result = process_followups()
        return Response(result, status=status.HTTP_200_OK)


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour visualiser et éditer les messages.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Déclenche l'envoi réel du message par email (via Brevo) en arrière-plan.
        """
        message = self.get_object()

        if message.status == 'SENT':
            return Response({'detail': 'Ce message a déjà été envoyé.'}, status=status.HTTP_400_BAD_REQUEST)

        if message.lead.unsubscribed:
            return Response(
                {'detail': "Ce prospect s'est désinscrit, l'envoi est bloqué."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message.status = 'QUEUED'
        message.save(update_fields=['status'])

        error = _delay_or_503(task_send_message, str(message.id))
        if error:
            message.status = 'FAILED'
            message.save(update_fields=['status'])
            return error

        return Response({'status': "Envoi en cours en arrière-plan"}, status=status.HTTP_202_ACCEPTED)


class AgentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint en lecture seule pour consulter les logs d'activité.
    """
    queryset = AgentLog.objects.all()
    serializer_class = AgentLogSerializer


@require_GET
def unsubscribe_view(request, lead_id):
    """
    Vue publique (lien cliqué depuis un email) permettant à un prospect de se désinscrire.
    """
    lead = Lead.objects.filter(id=lead_id).first()

    if lead is not None and not lead.unsubscribed:
        lead.unsubscribed = True
        lead.save(update_fields=['unsubscribed'])
        AgentLog.objects.create(
            action='LEAD_UNSUBSCRIBED',
            level='INFO',
            message=f"{lead.email} s'est désinscrit des communications.",
            lead=lead,
            campaign=lead.campaign,
        )

    return HttpResponse(
        "<html><body style='font-family:sans-serif;max-width:480px;margin:80px auto;text-align:center;color:#334155'>"
        "<h2>Vous avez bien été désinscrit</h2>"
        "<p>Vous ne recevrez plus de messages de notre part. Vous pouvez fermer cette page.</p>"
        "</body></html>"
    )
