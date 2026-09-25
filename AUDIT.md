# Audit technique — Mon Agent de Prospection

Date : 2026-09-23

## Vue d'ensemble de l'architecture

```
mon-agent-prospection/
├── backend/                  Django 5.2 + Django REST Framework + Celery
│   ├── core/                 Config projet (settings, urls, celery)
│   └── prospects/            App métier : Campaign, Lead, Message, AgentLog
└── frontend/                 React 19 + Vite (template par défaut, pas encore de vraie UI)
```

Le modèle de données (`Campaign` → `Lead` → `Message`, + `AgentLog` pour la traçabilité)
est cohérent et bien pensé pour un agent de prospection : statuts explicites, UUID en
clé primaire, champs orientés personnalisation IA (`ai_prompt_template`, `notes`, `score`).
La séparation vues / tâches Celery / service IA (`services/ai_agent.py`) suit une bonne
pratique (le gros risque — l'appel réseau vers Claude — tourne en tâche de fond au lieu
de bloquer la requête HTTP).

## Bugs corrigés

| # | Fichier | Problème | Impact | Correction |
|---|---------|----------|--------|------------|
| 1 | `backend/prospects/tasks.py` | Import de `generate_personalized_email`, fonction qui n'existe pas (`ai_agent.py` définit `generate_personalized_email_with_claude`) | La tâche Celery de génération IA plantait à coup sûr (`ImportError`) | Import corrigé vers le vrai nom de fonction |
| 2 | `backend/prospects/views.py` | Fichier entièrement dupliqué : imports, `CampaignViewSet`, `MessageViewSet`, `AgentLogViewSet` définis deux fois, plus un import mort vers la même fonction inexistante | Code source de confusion, risque de divergence entre les deux versions au fil des futures modifs | Fichier réécrit avec une seule version propre de chaque ViewSet |
| 3 | `backend/core/settings.py` | `CORS_ALLOW_ORIGINS` — ce réglage n'existe pas dans `django-cors-headers` (le bon nom est `CORS_ALLOWED_ORIGINS`) | **Toutes les requêtes du frontend (port 5173) étaient bloquées par CORS**, silencieusement | Renommé en `CORS_ALLOWED_ORIGINS` — vérifié : l'en-tête `Access-Control-Allow-Origin` est bien renvoyé maintenant |
| 4 | `backend/core/settings.py` | `filterset_fields` utilisé sur `LeadViewSet` mais `django-filter` n'était ni installé ni déclaré comme backend de filtrage DRF | Le filtrage par `?status=` ou `?campaign=` ne faisait strictement rien | Ajout de `django_filters` à `INSTALLED_APPS` + `DEFAULT_FILTER_BACKENDS` dans `REST_FRAMEWORK`, package installé |
| 5 | `backend/requirements.txt` | Fichier encodé en UTF-16LE au lieu d'UTF-8 (probablement généré par un éditeur/terminal Windows) | `pip install -r requirements.txt` échoue ou produit un fichier illisible pour la plupart des outils | Reconverti en UTF-8 ; ajout de `anthropic` et `django-filter`, qui étaient utilisés dans le code mais absents du fichier |
| 6 | Absent | Aucun `.gitignore` dans `backend/` | `venv/`, `db.sqlite3` et surtout `.env` (secrets) auraient été versionnés tels quels au premier `git init` / `git add` | `backend/.gitignore` créé |

Après ces corrections : `manage.py check` ne remonte aucune erreur, aucune migration
manquante, et les endpoints `/api/leads/` et `/api/campaigns/` répondent bien en 200
avec l'en-tête CORS attendu.

## ⚠️ Sécurité — action requise de ta part

`backend/.env` contient une **vraie clé API Anthropic en clair**. Comme ce fichier
n'était pas ignoré par git jusqu'ici, et qu'elle a été affichée dans cette session :

1. **Révoque cette clé** sur [console.anthropic.com](https://console.anthropic.com) et
   génère-en une nouvelle.
2. Colle la nouvelle clé uniquement dans `backend/.env` (maintenant ignoré par git).
3. Utilise `backend/.env.example` (créé, sans secret) comme référence pour toute
   nouvelle installation ou pour un collègue.

Le `SECRET_KEY` Django est également en dur dans `settings.py` — c'est normal et sans
risque en développement (`DEBUG=True`, usage local), mais à externaliser via
`DJANGO_SECRET_KEY` avant toute mise en production (le support est déjà en place dans
`settings.py`, il suffit de définir la variable d'environnement).

## État du frontend

Le frontend est encore le **template par défaut de Vite/React** (`App.jsx` affiche le
logo React/Vite de démonstration) — ce n'est pas un bug, simplement le prochain chantier
si tu avances pas à pas. `src/api/client.js` n'expose pour l'instant que 3 appels
(`getLeads`, `getCampaigns`, `generateAiMessage`) : il manquera le CRUD complet
(création/édition de campagnes et de leads, consultation des messages et des logs) pour
couvrir toute l'API déjà disponible côté backend.

## Recommandations pour la suite

- **Frontend** : construire les vues Campagnes / Leads / Messages / Logs consommant
  l'API existante (`/api/campaigns/`, `/api/leads/`, `/api/messages/`, `/api/logs/`).
- **Auth** : `DEFAULT_PERMISSION_CLASSES = AllowAny` — acceptable en dev solo, mais à
  restreindre avant toute exposition publique (au minimum `IsAuthenticated` + un système
  de login).
- **Tests** : `prospects/tests.py` est vide. Au minimum, couvrir la génération IA
  (mock de l'appel Anthropic) et les actions `start`/`pause` de campagne.
- **Prod** : penser à un vrai `DATABASE_URL` (Postgres) et à sortir `CELERY_BROKER_URL`
  du localhost en environnement de déploiement — déjà paramétrable via variables d'env
  suite aux corrections ci-dessus.
