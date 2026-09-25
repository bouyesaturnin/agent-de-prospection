from prospects.models import Campaign, Lead, Message


def make_campaign(**kwargs):
    defaults = {'name': 'Campagne Test', 'status': 'ACTIVE'}
    defaults.update(kwargs)
    return Campaign.objects.create(**defaults)


def make_lead(**kwargs):
    defaults = {
        'email': f'lead-{Lead.objects.count()}@example.com',
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'status': 'NEW',
    }
    defaults.update(kwargs)
    return Lead.objects.create(**defaults)


def make_message(lead, **kwargs):
    defaults = {
        'msg_type': 'EMAIL',
        'status': 'DRAFT',
        'subject': 'Sujet test',
        'body': 'Corps du message test.',
    }
    defaults.update(kwargs)
    return Message.objects.create(lead=lead, **defaults)
