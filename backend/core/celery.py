import os
from celery import Celery

# Définir le module de paramètres par défaut de Django pour 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Charger la configuration depuis settings.py en utilisant le préfixe CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger automatiquement les tâches (tasks.py) de toutes les applications installées
app.autodiscover_tasks()

# Tâches périodiques (nécessite un process `celery -A core beat`, ou `worker -B`
# en dev pour lancer worker + beat dans le même process).
app.conf.beat_schedule = {
    'check-email-replies-every-5-minutes': {
        'task': 'prospects.tasks.task_check_replies',
        'schedule': 300.0,
    },
    'process-followups-every-6-hours': {
        'task': 'prospects.tasks.task_process_followups',
        'schedule': 6 * 60 * 60.0,
    },
}