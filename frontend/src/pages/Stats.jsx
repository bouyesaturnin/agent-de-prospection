import { useEffect, useState } from 'react';
import { TrendingUp, CheckCircle2, AlertTriangle, Mail } from 'lucide-react';
import { getStats } from '../api/client';
import StatCard from '../components/StatCard';

const FUNNEL_ORDER = [
  { key: 'NEW', label: 'Nouveau', color: 'bg-slate-300' },
  { key: 'GENERATED', label: 'Message généré', color: 'bg-blue-400' },
  { key: 'CONTACTED', label: 'Contacté', color: 'bg-amber-400' },
  { key: 'REPLIED', label: 'A répondu', color: 'bg-purple-400' },
  { key: 'QUALIFIED', label: 'Qualifié', color: 'bg-emerald-500' },
  { key: 'UNQUALIFIED', label: 'Non intéressé', color: 'bg-rose-400' },
  { key: 'BOUNCED', label: 'Email invalide', color: 'bg-red-500' },
];

function formatPercent(value) {
  return value == null ? '—' : `${Math.round(value * 100)}%`;
}

function formatShortDate(isoDate) {
  const [, month, day] = isoDate.split('-');
  return `${day}/${month}`;
}

export default function Stats() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    getStats()
      .then((res) => setData(res.data))
      .catch(() => setErrorMsg('Impossible de charger les statistiques.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="flex-1 p-6">
        <div className="h-32 animate-pulse rounded-2xl bg-slate-100" />
      </main>
    );
  }

  if (errorMsg || !data) {
    return (
      <main className="flex-1 p-6">
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMsg || 'Aucune donnée.'}
        </p>
      </main>
    );
  }

  const { funnel, rates, messages_per_day: messagesPerDay, by_campaign: byCampaign } = data;
  const funnelTotal = Object.values(funnel).reduce((a, b) => a + b, 0);
  const totalSent30d = messagesPerDay.reduce((sum, d) => sum + d.sent, 0);
  const maxDaily = Math.max(1, ...messagesPerDay.map((d) => d.sent));

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur">
        <h1 className="text-xl font-bold text-slate-900">Statistiques</h1>
        <p className="text-sm text-slate-400">Vue d'ensemble de la performance de ta prospection.</p>
      </header>

      <main className="flex-1 space-y-6 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon={Mail} label="Emails envoyés (30j)" value={totalSent30d} accent="brand" />
          <StatCard
            icon={TrendingUp}
            label="Taux de réponse"
            value={formatPercent(rates.reply_rate)}
            hint="Parmi les prospects contactés"
            accent="emerald"
          />
          <StatCard
            icon={CheckCircle2}
            label="Taux de qualification"
            value={formatPercent(rates.qualification_rate)}
            hint="Parmi ceux qui ont répondu"
            accent="amber"
          />
          <StatCard
            icon={AlertTriangle}
            label="Taux de bounce"
            value={formatPercent(rates.bounce_rate)}
            hint="Adresses invalides"
            accent="rose"
          />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">Entonnoir de conversion</h2>
          <div className="mt-4 space-y-2.5">
            {FUNNEL_ORDER.map(({ key, label, color }) => {
              const count = funnel[key] || 0;
              const pct = funnelTotal ? (count / funnelTotal) * 100 : 0;
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="w-32 shrink-0 text-xs font-medium text-slate-500">{label}</span>
                  <div className="h-5 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full ${color} transition-all`}
                      style={{ width: `${Math.max(pct, count ? 2 : 0)}%` }}
                    />
                  </div>
                  <span className="w-10 shrink-0 text-right text-xs font-semibold text-slate-700">{count}</span>
                </div>
              );
            })}
          </div>
          {funnelTotal === 0 && (
            <p className="mt-3 text-center text-xs text-slate-400">
              Aucun prospect pour l'instant — importe ou découvre des prospects pour voir l'entonnoir se remplir.
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">Emails envoyés par jour (30 derniers jours)</h2>
          {messagesPerDay.length === 0 ? (
            <p className="mt-4 text-center text-xs text-slate-400">Aucun email envoyé sur cette période.</p>
          ) : (
            <div className="mt-4 flex h-40 items-end gap-1.5 overflow-x-auto pb-1">
              {messagesPerDay.map((d) => (
                <div key={d.date} className="flex min-w-[28px] flex-1 flex-col items-center gap-1">
                  <span className="text-[10px] font-semibold text-slate-600">{d.sent}</span>
                  <div
                    className="w-full rounded-t-md bg-brand-500"
                    style={{ height: `${Math.max((d.sent / maxDaily) * 100, 6)}%` }}
                    title={`${d.sent} email(s) le ${formatShortDate(d.date)}`}
                  />
                  <span className="text-[10px] text-slate-400">{formatShortDate(d.date)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <h2 className="px-5 pt-5 text-sm font-semibold text-slate-800">Détail par campagne</h2>
          {byCampaign.length === 0 ? (
            <p className="px-5 py-6 text-center text-xs text-slate-400">Aucune campagne créée pour l'instant.</p>
          ) : (
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-y border-slate-100 text-xs font-medium uppercase tracking-wide text-slate-400">
                    <th className="px-5 py-2">Campagne</th>
                    <th className="px-5 py-2">Prospects</th>
                    <th className="px-5 py-2">Contactés</th>
                    <th className="px-5 py-2">Réponses</th>
                    <th className="px-5 py-2">Qualifiés</th>
                  </tr>
                </thead>
                <tbody>
                  {byCampaign.map((c) => (
                    <tr key={c.id} className="border-b border-slate-50 last:border-0">
                      <td className="px-5 py-3 font-medium text-slate-800">{c.name}</td>
                      <td className="px-5 py-3 text-slate-600">{c.leads_count}</td>
                      <td className="px-5 py-3 text-slate-600">{c.contacted}</td>
                      <td className="px-5 py-3 text-slate-600">{c.replied}</td>
                      <td className="px-5 py-3 text-slate-600">{c.qualified}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
