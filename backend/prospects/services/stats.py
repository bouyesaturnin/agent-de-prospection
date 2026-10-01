from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from prospects.models import Campaign, Lead, Message

REPLIED_STATUSES = ['REPLIED', 'QUALIFIED', 'UNQUALIFIED']
CONTACTED_OR_LATER_STATUSES = ['CONTACTED'] + REPLIED_STATUSES

MESSAGES_PER_DAY_WINDOW_DAYS = 30


def compute_stats() -> dict:
    status_counts = dict(
        Lead.objects.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
    )
    funnel = {code: status_counts.get(code, 0) for code, _ in Lead.STATUS_CHOICES}

    contacted_total = sum(funnel[s] for s in CONTACTED_OR_LATER_STATUSES)
    replied_total = sum(funnel[s] for s in REPLIED_STATUSES)
    attempted_total = contacted_total + funnel['BOUNCED']

    rates = {
        'reply_rate': (replied_total / contacted_total) if contacted_total else None,
        'qualification_rate': (funnel['QUALIFIED'] / replied_total) if replied_total else None,
        'bounce_rate': (funnel['BOUNCED'] / attempted_total) if attempted_total else None,
    }

    since = timezone.now() - timedelta(days=MESSAGES_PER_DAY_WINDOW_DAYS)
    daily_rows = (
        Message.objects.filter(status='SENT', sent_at__gte=since)
        .annotate(day=TruncDate('sent_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    messages_per_day = [{'date': row['day'].isoformat(), 'sent': row['count']} for row in daily_rows]

    by_campaign = []
    for campaign in Campaign.objects.all().order_by('-created_at'):
        leads = campaign.leads.all()
        by_campaign.append({
            'id': str(campaign.id),
            'name': campaign.name,
            'leads_count': leads.count(),
            'contacted': leads.filter(status__in=CONTACTED_OR_LATER_STATUSES).count(),
            'replied': leads.filter(status__in=REPLIED_STATUSES).count(),
            'qualified': leads.filter(status='QUALIFIED').count(),
        })

    return {
        'funnel': funnel,
        'rates': rates,
        'messages_per_day': messages_per_day,
        'by_campaign': by_campaign,
    }
