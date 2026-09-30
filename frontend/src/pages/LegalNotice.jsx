import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export default function LegalNotice() {
  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="text-sm font-bold text-slate-900">ProspectAI</span>
        </div>

        <h1 className="text-xl font-bold text-slate-900">Mentions légales</h1>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Éditeur du site</h2>
          <p className="text-sm text-slate-600">
            Bouye Saturnin — Entrepreneur individuel (micro-entreprise)
            <br />
            SIRET : 882 044 514 00017
            <br />
            Adresse : 28 avenue Général Leclerc, 94470 Boissy-Saint-Léger, France
            <br />
            Email : <a className="text-brand-600 hover:underline" href="mailto:saturnin@mailagent-ia.eu">saturnin@mailagent-ia.eu</a>
            <br />
            Directeur de la publication : Bouye Saturnin
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Hébergement</h2>
          <p className="text-sm text-slate-600">
            Application (frontend) : Vercel Inc. — 340 S Lemon Ave #4133, Walnut, CA 91789, États-Unis —{' '}
            <a className="text-brand-600 hover:underline" href="https://vercel.com" target="_blank" rel="noreferrer">
              vercel.com
            </a>
            <br />
            Serveur et base de données (backend) : Railway Corporation — 251 Little Falls Drive, Wilmington, DE
            19808, États-Unis —{' '}
            <a className="text-brand-600 hover:underline" href="https://railway.com" target="_blank" rel="noreferrer">
              railway.com
            </a>
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Activité</h2>
          <p className="text-sm text-slate-600">
            Ce site est un outil interne de gestion de la prospection commerciale (création de sites web et agent
            d'automatisation par IA) utilisé par son éditeur. Il n'est pas ouvert à l'inscription publique.
          </p>
        </section>

        <section className="mt-6 space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Contact</h2>
          <p className="text-sm text-slate-600">
            Pour toute question relative à ce site ou aux emails que vous avez reçus, écrivez à{' '}
            <a className="text-brand-600 hover:underline" href="mailto:saturnin@mailagent-ia.eu">saturnin@mailagent-ia.eu</a>.
          </p>
        </section>

        <div className="mt-8 border-t border-slate-100 pt-4 text-sm">
          <Link to="/confidentialite" className="text-brand-600 hover:underline">
            Politique de confidentialité
          </Link>
        </div>
      </div>
    </div>
  );
}
