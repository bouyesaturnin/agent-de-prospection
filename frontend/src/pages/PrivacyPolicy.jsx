import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="text-sm font-bold text-slate-900">ProspectAI</span>
        </div>

        <h1 className="text-xl font-bold text-slate-900">Politique de confidentialité</h1>
        <p className="mt-1 text-sm text-slate-400">Dernière mise à jour : 30 septembre 2026</p>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Responsable du traitement</h2>
          <p className="text-sm text-slate-600">
            Bouye Saturnin, entrepreneur individuel (SIRET 882 044 514 00017), 28 avenue Général Leclerc, 94470
            Boissy-Saint-Léger —{' '}
            <a className="text-brand-600 hover:underline" href="mailto:saturnin@mailagent-ia.eu">saturnin@mailagent-ia.eu</a>
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Données collectées</h2>
          <p className="text-sm text-slate-600">
            Dans le cadre de sa démarche de prospection commerciale B2B, Bouye Saturnin collecte et traite des
            données professionnelles publiques ou obtenues directement auprès des entreprises contactées : nom,
            prénom, adresse email professionnelle, numéro de téléphone, nom de l'entreprise, poste occupé. Aucune
            donnée sensible n'est collectée.
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Finalité et base légale</h2>
          <p className="text-sm text-slate-600">
            Ces données sont utilisées exclusivement pour de la prospection commerciale entre professionnels
            (proposition de création de site web ou d'un agent d'automatisation par IA). Le traitement repose sur
            l'intérêt légitime de l'entreprise (article 6.1.f du RGPD), conformément aux recommandations de la CNIL
            sur la prospection commerciale par email entre professionnels (B2B).
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Durée de conservation</h2>
          <p className="text-sm text-slate-600">
            Les données sont conservées le temps de la démarche commerciale, et supprimées sans délai en cas de
            désinscription ou de demande explicite.
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Destinataires</h2>
          <p className="text-sm text-slate-600">
            Les données ne sont ni vendues ni partagées avec des tiers à des fins commerciales. Elles sont hébergées
            chez Vercel Inc. et Railway Corporation, sous-traitants techniques (hébergement uniquement, voir les{' '}
            <Link to="/mentions-legales" className="text-brand-600 hover:underline">mentions légales</Link>), et
            transitent par Brevo pour l'envoi des emails.
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Vos droits</h2>
          <p className="text-sm text-slate-600">
            Conformément au RGPD, vous disposez d'un droit d'accès, de rectification, d'effacement et d'opposition
            sur vos données. Vous pouvez vous désinscrire à tout moment via le lien présent dans chaque email reçu,
            ou exercer vos droits en écrivant à{' '}
            <a className="text-brand-600 hover:underline" href="mailto:saturnin@mailagent-ia.eu">saturnin@mailagent-ia.eu</a>.
            Vous disposez également d'un droit de réclamation auprès de la CNIL (
            <a className="text-brand-600 hover:underline" href="https://www.cnil.fr" target="_blank" rel="noreferrer">
              cnil.fr
            </a>
            ).
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Sécurité</h2>
          <p className="text-sm text-slate-600">
            Les échanges avec ce site sont chiffrés (HTTPS) et l'accès à l'outil de gestion est protégé par
            authentification. Aucun cookie de suivi publicitaire n'est utilisé sur les pages publiques de ce site.
          </p>
        </section>

        <div className="mt-8 border-t border-slate-100 pt-4 text-sm">
          <Link to="/mentions-legales" className="text-brand-600 hover:underline">
            Mentions légales
          </Link>
        </div>
      </div>
    </div>
  );
}
