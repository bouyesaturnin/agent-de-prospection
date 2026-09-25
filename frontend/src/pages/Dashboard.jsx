import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Users,
  Sparkles,
  Megaphone,
  MailCheck,
  RefreshCw,
  Search,
  Mail,
  Building2,
  ChevronLeft,
  ChevronRight,
  Plus,
  Upload,
  Inbox,
  Repeat,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { getLeads, getCampaigns, getLogs, generateAiMessage, checkReplies, processFollowups } from '../api/client';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import ActivityFeed from '../components/ActivityFeed';
import LeadFormModal from '../components/LeadFormModal';
import LeadDetailModal from '../components/LeadDetailModal';
import ImportCsvModal from '../components/ImportCsvModal';

const STATUS_OPTIONS = [
  { value: '', label: 'Tous les statuts' },
  { value: 'NEW', label: 'Nouveau' },
  { value: 'GENERATED', label: 'Message généré' },
  { value: 'CONTACTED', label: 'Contacté' },
  { value: 'REPLIED', label: 'A répondu' },
  { value: 'QUALIFIED', label: 'Qualifié' },
  { value: 'UNQUALIFIED', label: 'Non intéressé' },
  { value: 'BOUNCED', label: 'Email invalide' },
];

function initials(lead) {
  const a = lead.first_name?.[0] || lead.email?.[0] || '?';
  const b = lead.last_name?.[0] || '';
  return (a + b).toUpperCase();
}

export default function Dashboard() {
  const [leads, setLeads] = useState([]);
  const [leadsCount, setLeadsCount] = useState(0);
  const [campaigns, setCampaigns] = useState([]);
  const [logs, setLogs] = useState([]);

  const [loadingLeads, setLoadingLeads] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [generatingId, setGeneratingId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [infoMsg, setInfoMsg] = useState('');
  const [checkingReplies, setCheckingReplies] = useState(false);
  const [processingFollowups, setProcessingFollowups] = useState(false);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [campaignFilter, setCampaignFilter] = useState('');
  const [page, setPage] = useState(1);

  const [createOpen, setCreateOpen] = useState(false);
  const [editingLeadId, setEditingLeadId] = useState(null);
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [importOpen, setImportOpen] = useState(false);

  const fetchLeads = useCallback(async () => {
    try {
      setLoadingLeads(true);
      const params = { page };
      if (statusFilter) params.status = statusFilter;
      if (campaignFilter) params.campaign = campaignFilter;
      const response = await getLeads(params);
      const data = response.data;
      setLeads(data.results ?? data);
      setLeadsCount(data.count ?? (data.results ?? data).length);
      setErrorMsg('');
    } catch (error) {
      console.error('Erreur lors du chargement des prospects :', error);
      setErrorMsg("Impossible de contacter l'API. Vérifie que le serveur Django tourne bien.");
    } finally {
      setLoadingLeads(false);
    }
  }, [page, statusFilter, campaignFilter]);

  const fetchCampaigns = useCallback(async () => {
    try {
      const response = await getCampaigns();
      setCampaigns(response.data.results ?? response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des campagnes :', error);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      setLoadingLogs(true);
      const response = await getLogs({ page: 1 });
      setLogs((response.data.results ?? response.data).slice(0, 8));
    } catch (error) {
      console.error('Erreur lors du chargement des journaux :', error);
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  useEffect(() => {
    fetchCampaigns();
    fetchLogs();
  }, [fetchCampaigns, fetchLogs]);

  const handleGenerateAi = async (leadId) => {
    try {
      setGeneratingId(leadId);
      await generateAiMessage(leadId);
      await fetchLeads();
      await fetchLogs();
    } catch (error) {
      console.error(error);
      setErrorMsg('Échec de la génération du message IA pour ce prospect.');
    } finally {
      setGeneratingId(null);
    }
  };

  const refreshAll = () => {
    fetchLeads();
    fetchCampaigns();
    fetchLogs();
  };

  const handleCheckReplies = async () => {
    setCheckingReplies(true);
    setErrorMsg('');
    setInfoMsg('');
    try {
      const response = await checkReplies();
      const { matched, ignored } = response.data;
      setInfoMsg(
        matched > 0
          ? `${matched} nouvelle(s) réponse(s) détectée(s) (${ignored} email(s) sans prospect associé ignoré(s)).`
          : `Aucune nouvelle réponse pour le moment (${ignored} email(s) ignoré(s)).`
      );
      await fetchLeads();
      await fetchLogs();
    } catch (error) {
      setErrorMsg(error.response?.data?.detail || 'Échec de la vérification des réponses.');
    } finally {
      setCheckingReplies(false);
    }
  };

  const handleProcessFollowups = async () => {
    setProcessingFollowups(true);
    setErrorMsg('');
    setInfoMsg('');
    try {
      const response = await processFollowups();
      const { created, skipped } = response.data;
      setInfoMsg(
        created > 0
          ? `${created} relance(s) générée(s) en brouillon — à valider dans la fiche de chaque prospect.`
          : `Aucune relance à générer pour le moment (${skipped} prospect(s) pas encore éligible(s) ou déjà en attente).`
      );
      await fetchLeads();
      await fetchLogs();
    } catch (error) {
      setErrorMsg(error.response?.data?.detail || 'Échec de la génération des relances.');
    } finally {
      setProcessingFollowups(false);
    }
  };

  const filteredLeads = useMemo(() => {
    if (!search.trim()) return leads;
    const q = search.trim().toLowerCase();
    return leads.filter((lead) =>
      [lead.first_name, lead.last_name, lead.email, lead.company]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(q))
    );
  }, [leads, search]);

  const stats = useMemo(() => {
    const newLeads = leads.filter((l) => l.status === 'NEW').length;
    const messagesGenerated = leads.reduce((acc, l) => acc + (l.messages?.length || 0), 0);
    const activeCampaigns = campaigns.filter((c) => c.status === 'ACTIVE').length;
    return { newLeads, messagesGenerated, activeCampaigns };
  }, [leads, campaigns]);

  const campaignName = (campaignId) => campaigns.find((c) => c.id === campaignId)?.name;
  const editingLead = leads.find((l) => l.id === editingLeadId) || null;
  const selectedLead = leads.find((l) => l.id === selectedLeadId) || null;

  const pageSize = 20;
  const totalPages = Math.max(1, Math.ceil(leadsCount / pageSize));

  return (
    <>
      {/* Topbar */}
      <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-400">Vue d'ensemble de votre prospection</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refreshAll}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" /> Actualiser
          </button>
          <button
            onClick={() => setImportOpen(true)}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            <Upload className="h-4 w-4" /> Importer CSV
          </button>
          <button
            onClick={handleCheckReplies}
            disabled={checkingReplies}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-60"
          >
            <Inbox className={`h-4 w-4 ${checkingReplies ? 'animate-pulse' : ''}`} />
            {checkingReplies ? 'Vérification...' : 'Vérifier les réponses'}
          </button>
          <button
            onClick={handleProcessFollowups}
            disabled={processingFollowups}
            title="Génère des brouillons de relance pour les prospects contactés sans réponse — rien n'est envoyé automatiquement"
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-60"
          >
            <Repeat className={`h-4 w-4 ${processingFollowups ? 'animate-spin' : ''}`} />
            {processingFollowups ? 'Génération...' : 'Générer les relances'}
          </button>
          <button
            onClick={() => setCreateOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Nouveau prospect
          </button>
        </div>
      </header>

      <main className="flex-1 space-y-6 p-6">
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

        {/* KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={Users} label="Prospects au total" value={leadsCount} accent="brand" />
          <StatCard icon={Sparkles} label="Nouveaux prospects" value={stats.newLeads} accent="amber" />
          <StatCard icon={MailCheck} label="Messages générés" value={stats.messagesGenerated} accent="emerald" />
          <StatCard icon={Megaphone} label="Campagnes actives" value={stats.activeCampaigns} accent="rose" />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Leads table */}
          <div className="lg:col-span-2">
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
              {/* Filters */}
              <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Rechercher un prospect, une entreprise..."
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-700 outline-none focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setPage(1);
                    setStatusFilter(e.target.value);
                  }}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none focus:border-brand-400 focus:bg-white"
                >
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <select
                  value={campaignFilter}
                  onChange={(e) => {
                    setPage(1);
                    setCampaignFilter(e.target.value);
                  }}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none focus:border-brand-400 focus:bg-white"
                >
                  <option value="">Toutes les campagnes</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs font-semibold uppercase tracking-wider text-slate-400">
                      <th className="px-4 py-3">Prospect</th>
                      <th className="px-4 py-3">Entreprise</th>
                      <th className="px-4 py-3">Statut</th>
                      <th className="px-4 py-3">Dernier message</th>
                      <th className="px-4 py-3 text-right">Action IA</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 text-sm">
                    {loadingLeads ? (
                      [...Array(5)].map((_, i) => (
                        <tr key={i}>
                          <td colSpan={5} className="px-4 py-4">
                            <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
                          </td>
                        </tr>
                      ))
                    ) : filteredLeads.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-12 text-center text-slate-400">
                          Aucun prospect ne correspond à ces critères.
                        </td>
                      </tr>
                    ) : (
                      filteredLeads.map((lead) => {
                        const lastMessage = lead.messages?.[0];
                        return (
                          <tr
                            key={lead.id}
                            onClick={() => setSelectedLeadId(lead.id)}
                            className="cursor-pointer transition hover:bg-slate-50/70"
                          >
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                                  {initials(lead)}
                                </div>
                                <div className="min-w-0">
                                  <p className="truncate font-medium text-slate-900">
                                    {lead.first_name} {lead.last_name}
                                  </p>
                                  <p className="flex items-center gap-1 truncate text-xs text-slate-400">
                                    <Mail className="h-3 w-3 shrink-0" /> {lead.email}
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-3.5">
                              <p className="text-slate-700">{lead.job_title || '—'}</p>
                              <p className="flex items-center gap-1 text-xs text-slate-400">
                                <Building2 className="h-3 w-3 shrink-0" /> {lead.company || 'Non renseignée'}
                              </p>
                            </td>
                            <td className="px-4 py-3.5">
                              <StatusBadge status={lead.status} label={lead.status_display} />
                            </td>
                            <td className="max-w-55 px-4 py-3.5">
                              {lastMessage ? (
                                <p className="truncate text-xs text-slate-600" title={lastMessage.body}>
                                  <span className="font-semibold text-slate-800">{lastMessage.subject} : </span>
                                  {lastMessage.body}
                                </p>
                              ) : (
                                <span className="text-xs italic text-slate-300">Aucun message</span>
                              )}
                            </td>
                            <td className="px-4 py-3.5 text-right">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleGenerateAi(lead.id);
                                }}
                                disabled={generatingId === lead.id}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-brand-300"
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                                {generatingId === lead.id ? 'Génération...' : 'Générer'}
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {!loadingLeads && leadsCount > pageSize && (
                <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
                  <span>
                    Page {page} sur {totalPages} · {leadsCount} prospects
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                      className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 disabled:opacity-40"
                    >
                      <ChevronLeft className="h-4 w-4" /> Précédent
                    </button>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                      className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 disabled:opacity-40"
                    >
                      Suivant <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Activity feed */}
          <div>
            <ActivityFeed logs={logs} loading={loadingLogs} />
          </div>
        </div>
      </main>

      <LeadFormModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSaved={fetchLeads}
        campaigns={campaigns}
        lead={null}
      />

      <LeadFormModal
        open={Boolean(editingLeadId)}
        onClose={() => setEditingLeadId(null)}
        onSaved={fetchLeads}
        campaigns={campaigns}
        lead={editingLead}
      />

      <LeadDetailModal
        open={Boolean(selectedLeadId)}
        onClose={() => setSelectedLeadId(null)}
        lead={selectedLead}
        campaignName={selectedLead ? campaignName(selectedLead.campaign) : null}
        onEdit={(lead) => {
          setSelectedLeadId(null);
          setEditingLeadId(lead.id);
        }}
        onChanged={fetchLeads}
      />

      <ImportCsvModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={fetchLeads}
        campaigns={campaigns}
      />
    </>
  );
}
