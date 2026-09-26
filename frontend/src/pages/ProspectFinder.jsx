import { useCallback, useEffect, useState } from 'react';
import {
  Search,
  MapPin,
  Phone,
  Loader2,
  AlertCircle,
  CheckCircle2,
  UserPlus,
  X,
  Building2,
} from 'lucide-react';
import {
  getDiscoveredProspects,
  searchProspects,
  updateDiscoveredProspect,
  convertDiscoveredProspect,
  getCampaigns,
} from '../api/client';

const TABS = [
  { value: 'NEW', label: 'À qualifier' },
  { value: 'CONVERTED', label: 'Convertis' },
  { value: 'DISCARDED', label: 'Écartés' },
];

export default function ProspectFinder() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [searching, setSearching] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [infoMsg, setInfoMsg] = useState('');

  const [tab, setTab] = useState('NEW');
  const [prospects, setProspects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [campaigns, setCampaigns] = useState([]);

  const [emailDrafts, setEmailDrafts] = useState({});
  const [campaignChoice, setCampaignChoice] = useState({});
  const [busyId, setBusyId] = useState(null);

  const fetchProspects = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getDiscoveredProspects({ status: tab });
      setProspects(response.data.results ?? response.data);
    } catch (error) {
      console.error(error);
      setErrorMsg("Impossible de charger les prospects découverts.");
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    fetchProspects();
  }, [fetchProspects]);

  useEffect(() => {
    getCampaigns()
      .then((res) => setCampaigns(res.data.results ?? res.data))
      .catch(() => {});
  }, []);

  // Sans campagne, l'IA n'a aucune instruction (argument prix/délai/offre) et
  // génère un message générique : on présélectionne la campagne active pour
  // qu'un oubli de clic ne produise plus un email sans argumentaire.
  const defaultCampaignId = campaigns.find((c) => c.status === 'ACTIVE')?.id || '';

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setErrorMsg('');
    setInfoMsg('');
    try {
      const response = await searchProspects(query.trim(), location.trim());
      const { found, without_website, created, duplicates } = response.data;
      setInfoMsg(
        `${found} établissement(s) trouvé(s), ${without_website} sans site web ` +
          `(${created} nouveau(x), ${duplicates} déjà connu(s)).`
      );
      setTab('NEW');
      await fetchProspects();
    } catch (error) {
      setErrorMsg(error.response?.data?.detail || 'Échec de la recherche.');
    } finally {
      setSearching(false);
    }
  };

  const handleEmailChange = (id, value) => setEmailDrafts((d) => ({ ...d, [id]: value }));

  const handleConvert = async (prospect) => {
    const email = (emailDrafts[prospect.id] ?? prospect.email ?? '').trim();
    if (!email) {
      setErrorMsg('Renseigne un email avant de convertir ce prospect.');
      return;
    }
    setBusyId(prospect.id);
    setErrorMsg('');
    try {
      if (email !== prospect.email) {
        await updateDiscoveredProspect(prospect.id, { email });
      }
      const campaignId = campaignChoice[prospect.id] ?? defaultCampaignId;
      await convertDiscoveredProspect(prospect.id, campaignId || null);
      setInfoMsg(`${prospect.name} converti en prospect.`);
      await fetchProspects();
    } catch (error) {
      setErrorMsg(error.response?.data?.detail || 'Échec de la conversion.');
    } finally {
      setBusyId(null);
    }
  };

  const handleDiscard = async (prospect) => {
    setBusyId(prospect.id);
    try {
      await updateDiscoveredProspect(prospect.id, { status: 'DISCARDED' });
      await fetchProspects();
    } finally {
      setBusyId(null);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur">
        <h1 className="text-xl font-bold text-slate-900">Recherche de prospects</h1>
        <p className="text-sm text-slate-400">
          Trouve automatiquement des établissements sans site web (via Google Places) à qualifier puis convertir en prospects.
        </p>
      </header>

      <main className="flex-1 space-y-6 p-6">
        <form
          onSubmit={handleSearch}
          className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-end"
        >
          <div className="flex-1">
            <label className="text-xs font-medium text-slate-500">Métier / catégorie</label>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ex : restaurant, plombier, coiffeur..."
              required
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
          <div className="flex-1">
            <label className="text-xs font-medium text-slate-500">Ville / zone</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Ex : Boulogne-Billancourt"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Rechercher
          </button>
        </form>

        {errorMsg && (
          <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {errorMsg}
          </div>
        )}
        {infoMsg && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {infoMsg}
          </div>
        )}

        <div className="flex gap-1 border-b border-slate-200">
          {TABS.map((t) => (
            <button
              key={t.value}
              onClick={() => setTab(t.value)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
                tab === t.value
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          {loading ? (
            [...Array(3)].map((_, i) => <div key={i} className="h-24 animate-pulse rounded-2xl bg-slate-100" />)
          ) : prospects.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-12 text-center text-sm text-slate-400">
              {tab === 'NEW'
                ? "Aucun prospect à qualifier pour l'instant — lance une recherche ci-dessus."
                : 'Rien ici pour le moment.'}
            </div>
          ) : (
            prospects.map((p) => (
              <div key={p.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 shrink-0 text-slate-400" />
                      <p className="font-semibold text-slate-900">{p.name}</p>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
                      {p.address && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" /> {p.address}
                        </span>
                      )}
                      {p.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="h-3 w-3" /> {p.phone}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">
                    {p.category} · {p.search_location}
                  </span>
                </div>

                {tab === 'NEW' && (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
                    <input
                      type="email"
                      placeholder="Email du prospect (à trouver manuellement)"
                      value={emailDrafts[p.id] ?? p.email ?? ''}
                      onChange={(e) => handleEmailChange(p.id, e.target.value)}
                      className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                    />
                    <select
                      value={campaignChoice[p.id] ?? defaultCampaignId}
                      onChange={(e) => setCampaignChoice((c) => ({ ...c, [p.id]: e.target.value }))}
                      className="rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs outline-none focus:border-brand-400"
                    >
                      <option value="">Aucune campagne</option>
                      {campaigns.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleConvert(p)}
                      disabled={busyId === p.id}
                      className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                    >
                      {busyId === p.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <UserPlus className="h-3.5 w-3.5" />
                      )}
                      Convertir
                    </button>
                    <button
                      onClick={() => handleDiscard(p)}
                      disabled={busyId === p.id}
                      title="Écarter"
                      className="rounded-lg border border-slate-200 p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-600 disabled:opacity-60"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </main>
    </>
  );
}
