# Agent de Prospection

Agent de prospection B2B assisté par IA : génération de messages personnalisés (Claude),
envoi par email (Brevo), détection automatique des réponses (IMAP) et relances de suivi
en brouillon.

## En ligne

- **Application** : https://mailagent-ia.eu
- **API** : https://api.mailagent-ia.eu/api/

(Domaines par défaut, toujours actifs en secours : https://frontend-puce-two-67.vercel.app et https://backend-web-production-74ff.up.railway.app)

## Stack

- **Backend** : Django REST Framework + Celery (worker + beat) + Redis + PostgreSQL
- **Frontend** : React + Vite + Tailwind CSS
- **Hébergement** : Railway (backend, worker, beat, Postgres, Redis) + Vercel (frontend)

## Développement local

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # puis renseigner les clés API
python manage.py migrate
python manage.py runserver

# Celery (2 terminaux séparés)
celery -A core worker --loglevel=info --pool=solo   # --pool=solo requis sur Windows
celery -A core beat --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
python manage.py test prospects -v 2
```

La suite (57 tests) mocke systématiquement les services externes (Anthropic, Brevo,
IMAP) : aucun test ne fait de vrai appel réseau, même avec de vraies clés dans `.env`.

Un hook pre-commit (`.githooks/`, activé via `git config core.hooksPath .githooks`)
lance cette suite avant chaque commit. Un workflow GitHub Actions
(`.github/workflows/tests.yml`) la relance sur chaque push/pull request, en plus du
lint et du build du frontend.

## Déploiement

Le backend (Railway) et le frontend (Vercel) sont tous les deux connectés au dépôt
GitHub : un `git push` sur `main` redéploie automatiquement les deux.
