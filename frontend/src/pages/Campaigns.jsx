import { useCallback, useEffect, useState } from 'react';
import { Plus, Play, Pause, Users, Repeat, Pencil, Trash2, RefreshCw, AlertCircle } from 'lucide-react';
import CampaignFormModal from '../components/CampaignFormModal';
import { getCampaigns, startCampaign, pauseCampaign, deleteCampaign } from '../api/client';

const STATUS_STYLES = {
  DRAFT: 'bg-slate-100 text-slate-600 ring-slate-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  PAUSED: 'bg-amber-50 text-amber-700 ring-amber-200',
  COMPLETED: 'bg-blue-50 text-blue-700 ring-blue-200',
};

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const fetchCampaigns = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getCampaigns();
      setCampaigns(response.data.results ?? response.data);
      setErrorMsg('');
    } catch (error) {
      console.error(error);
      setErrorMsg("Impossible de contacter l'API. Vérifie que le serveur Django tourne bien.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const handleToggleStatus = async (campaign) => {
    setBusyId(campaign.id);
    try {
      if (campaign.status === 'ACTIVE') {
        await pauseCampaign(campaign.id);
      } else {
        await startCampaign(campaign.id);
      }
      await fetchCampaigns();
    } catch (error) {
      console.error(error);
      setErrorMsg("Échec de la mise à jour du statut de la campagne.");
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (campaignId) => {
    setBusyId(campaignId);
    try {
      await deleteCampaign(campaignId);
      await fetchCampaigns();
    } finally {
      setBusyId(null);
      setConfirmDeleteId(null);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Campagnes</h1>
            <p className="text-sm text-slate-400">Organise tes prospects et leurs instructions IA dédiées</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchCampaigns}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" /> Actualiser
            </button>
            <button
              onClick={() => {
                setEditingCampaign(null);
                setFormOpen(true);
              }}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              <Plus className="h-4 w-4" /> Nouvelle campagne
            </button>
          </div>
        </header>

        <main className="flex-1 space-y-4 p-6">
          {errorMsg && (
            <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {errorMsg}
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-40 animate-pulse rounded-2xl bg-slate-100" />
              ))}
            </div>
          ) : campaigns.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-12 text-center">
              <p className="text-sm text-slate-500">Aucune campagne pour le moment.</p>
              <button
                onClick={() => {
                  setEditingCampaign(null);
                  setFormOpen(true);
                }}
                className="mt-3 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                <Plus className="h-4 w-4" /> Créer ma première campagne
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {campaigns.map((campaign) => (
                <div key={campaign.id} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-slate-900">{campaign.name}</h3>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${
                        STATUS_STYLES[campaign.status] || STATUS_STYLES.DRAFT
                      }`}
                    >
                      {campaign.status_display}
                    </span>
                  </div>

                  <p className="mt-2 line-clamp-2 flex-1 text-sm text-slate-500">
                    {campaign.description || 'Aucune description.'}
                  </p>

                  <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5" /> {campaign.leads_count} prospect(s)
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Repeat className="h-3.5 w-3.5" /> Relance à {campaign.followup_delay_days}j (max{' '}
                      {campaign.max_followups})
                    </span>
                  </div>

                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                    {confirmDeleteId === campaign.id ? (
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-slate-500">Supprimer ?</span>
                        <button
                          onClick={() => handleDelete(campaign.id)}
                          className="rounded-md bg-red-600 px-2 py-1 font-semibold text-white"
                        >
                          Oui
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="rounded-md border border-slate-200 px-2 py-1 text-slate-600"
                        >
                          Non
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(campaign.id)}
                        className="flex items-center gap-1 text-xs font-medium text-red-500 hover:text-red-600"
                      >
                        <Trash2 className="h-3.5 w-3.5" /> Supprimer
                      </button>
                    )}

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setEditingCampaign(campaign);
                          setFormOpen(true);
                        }}
                        className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                      >
                        <Pencil className="h-3.5 w-3.5" /> Éditer
                      </button>
                      <button
                        onClick={() => handleToggleStatus(campaign)}
                        disabled={busyId === campaign.id || campaign.status === 'COMPLETED'}
                        className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-white disabled:opacity-50 ${
                          campaign.status === 'ACTIVE' ? 'bg-amber-500 hover:bg-amber-600' : 'bg-emerald-600 hover:bg-emerald-700'
                        }`}
                      >
                        {campaign.status === 'ACTIVE' ? (
                          <>
                            <Pause className="h-3.5 w-3.5" /> Pause
                          </>
                        ) : (
                          <>
                            <Play className="h-3.5 w-3.5" /> Démarrer
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
      </main>

      <CampaignFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={fetchCampaigns}
        campaign={editingCampaign}
      />
    </>
  );
}
