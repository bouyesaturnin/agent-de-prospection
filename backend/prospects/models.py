import uuid
from django.db import models


class Campaign(models.Model):
    """
    Représente une campagne de prospection ciblée.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('ACTIVE', 'En cours'),
        ('PAUSED', 'En pause'),
        ('COMPLETED', 'Terminée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nom de la campagne")
    description = models.TextField(blank=True, verbose_name="Description / Objectif")
    
    # Prompt de départ pour l'IA spécifique à cette campagne
    ai_prompt_template = models.TextField(
        blank=True, 
        help_text="Instructions/Prompt pour le LLM lors de la génération de messages pour cette campagne."
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Relances automatiques (générées en brouillon, jamais envoyées sans validation manuelle)
    followup_delay_days = models.PositiveIntegerField(
        default=3,
        verbose_name="Délai avant relance (jours)",
        help_text="Nombre de jours sans réponse avant qu'une relance soit générée automatiquement.",
    )
    max_followups = models.PositiveIntegerField(
        default=2,
        verbose_name="Nombre max de relances",
        help_text="Nombre maximum de relances automatiques générées par prospect.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Campagne"
        verbose_name_plural = "Campagnes"

    def __str__(self):
        return self.name


class Lead(models.Model):
    """
    Représente un prospect à contacter.
    """
    STATUS_CHOICES = [
        ('NEW', 'Nouveau / Non contacté'),
        ('GENERATED', 'Message généré par l\'IA'),
        ('CONTACTED', 'Contacté'),
        ('REPLIED', 'A répondu'),
        ('QUALIFIED', 'Qualifié / Intéressé'),
        ('UNQUALIFIED', 'Non intéressé'),
        ('BOUNCED', 'Email Invalide / Erreur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        related_name='leads',
        null=True,
        blank=True
    )

    # Informations d'identité
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")

    # Informations professionnelles (utiles pour l'IA et la personnalisation)
    company = models.CharField(max_length=150, blank=True, verbose_name="Entreprise")
    job_title = models.CharField(max_length=150, blank=True, verbose_name="Poste / Titre")
    linkedin_url = models.URLField(blank=True, verbose_name="Profil LinkedIn")
    website = models.URLField(blank=True, verbose_name="Site Web")

    # Métadonnées d'enrichissement & scoring
    notes = models.TextField(blank=True, help_text="Notes supplémentaires sur le prospect ou données collectées.")
    score = models.IntegerField(default=0, help_text="Score de pertinence calculé par l'IA ou règles métier.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    unsubscribed = models.BooleanField(
        default=False,
        verbose_name="Désinscrit",
        help_text="Le prospect s'est désinscrit : ne plus lui envoyer de message.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email


class Message(models.Model):
    """
    Stocke l'historique des échanges/messages générés ou envoyés à un prospect.
    """
    TYPE_CHOICES = [
        ('EMAIL', 'Email'),
        ('LINKEDIN', 'Message LinkedIn'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Généré (Brouillon)'),
        ('QUEUED', 'En attente d\'envoi'),
        ('SENT', 'Envoyé'),
        ('FAILED', 'Échec de l\'envoi'),
        ('RECEIVED', 'Réponse reçue du prospect'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages')
    
    msg_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='EMAIL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    subject = models.CharField(max_length=255, blank=True, verbose_name="Sujet")
    body = models.TextField(verbose_name="Corps du message")

    # Méta-informations d'envoi et d'IA
    generated_by_ai = models.BooleanField(default=True, verbose_name="Généré par l'IA")
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.get_msg_type_display()} - {self.lead} [{self.get_status_display()}]"


class AgentLog(models.Model):
    """
    Journal d'exécution pour suivre les actions automatiques de l'agent (Scraping, IA, Envois).
    """
    LEVEL_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=100, help_text="Ex: 'SCRAPING_COMPLETED', 'AI_MESSAGE_GENERATED', 'EMAIL_SENT'")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    message = models.TextField()
    
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.action} - {self.level}"


class DiscoveredProspect(models.Model):
    """
    Résultat brut d'une recherche automatique (Google Places) : une entreprise
    sans site web détectée, en attente qu'un email lui soit associé à la main
    avant de pouvoir devenir un vrai Lead exploitable par l'agent.
    """
    STATUS_CHOICES = [
        ('NEW', 'À qualifier'),
        ('CONVERTED', 'Converti en prospect'),
        ('DISCARDED', 'Écarté'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_place_id = models.CharField(max_length=255, unique=True)

    name = models.CharField(max_length=255, verbose_name="Nom de l'entreprise")
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=150, blank=True, help_text="Terme de recherche utilisé, ex: 'restaurant'")
    search_location = models.CharField(max_length=150, blank=True, help_text="Ville/zone utilisée pour la recherche")

    email = models.EmailField(blank=True, verbose_name="Email (à compléter manuellement)")
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    converted_lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='discovery_source'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Prospect découvert"
        verbose_name_plural = "Prospects découverts"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ImapSyncState(models.Model):
    """
    Retient le dernier UID IMAP traité pour une boîte donnée, afin que le relevé
    des réponses ne reparcoure jamais tout l'historique de la boîte mail (qui peut
    contenir des dizaines de milliers d'emails personnels sans rapport).
    """
    mailbox_key = models.CharField(max_length=255, unique=True, help_text="host:username:dossier")
    last_uid = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mailbox_key} -> UID {self.last_uid}"