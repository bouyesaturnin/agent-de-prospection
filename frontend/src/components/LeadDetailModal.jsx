import { useEffect, useRef, useState } from 'react';
import {
  Mail,
  Building2,
  Briefcase,
  Phone,
  Link as LinkIcon,
  Trash2,
  Pencil,
  Sparkles,
  Loader2,
  Send,
  BellOff,
  AlertTriangle,
} from 'lucide-react';
import Modal from './Modal';
import StatusBadge from './StatusBadge';
import { deleteLead, generateAiMessage, sendMessage, updateMessage } from '../api/client';

const MESSAGE_STATUS_LABEL = {
  DRAFT: 'Brouillon',
  QUEUED: "En attente d'envoi",
  SENT: 'Envoyé',
  FAILED: 'Échec',
  RECEIVED: 'Réponse reçue',
};

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 10; // ~20s : la génération prend en général 3-5s

export default function LeadDetailModal({ open, onClose, lead, campaignName, onEdit, onChanged }) {
  const [deleting, setDeleting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generateTimedOut, setGenerateTimedOut] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [sendingId, setSendingId] = useState(null);
  const [sendError, setSendError] = useState('');
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState('');

  const messageCountBeforeGenerate = useRef(0);
  const messageArrivedRef = useRef(false);

  // Dès que le nombre de messages augmente pendant une génération en cours, on
  // sait que le brouillon est arrivé : on arrête le spinner tout seul, sans
  // attendre le prochain rafraîchissement manuel.
  useEffect(() => {
    if (generating && (lead?.messages?.length || 0) > messageCountBeforeGenerate.current) {
      messageArrivedRef.current = true;
      setGenerating(false);
    }
  }, [lead?.messages?.length, generating]);

  if (!lead) return null;

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteLead(lead.id);
      onChanged();
      onClose();
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const handleGenerate = async () => {
    messageCountBeforeGenerate.current = lead.messages?.length || 0;
    messageArrivedRef.current = false;
    setGenerating(true);
    setGenerateTimedOut(false);
    try {
      await generateAiMessage(lead.id);
    } catch {
      setGenerating(false);
      return;
    }

    // La génération tourne en arrière-plan (Celery, ~3-5s) : on interroge le
    // serveur à intervalles réguliers jusqu'à voir apparaître le nouveau
    // message (détecté par l'effet ci-dessus), plutôt que de rafraîchir une
    // seule fois trop tôt.
    for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
      if (messageArrivedRef.current) return;
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      await onChanged();
    }
    if (!messageArrivedRef.current) {
      setGenerating(false);
      setGenerateTimedOut(true);
    }
  };

  const startEdit = (msg) => {
    setEditingMessageId(msg.id);
    setEditSubject(msg.subject || '');
    setEditBody(msg.body || '');
    setEditError('');
  };

  const cancelEdit = () => {
    setEditingMessageId(null);
    setEditError('');
  };

  const handleSaveEdit = async (messageId) => {
    setSavingEdit(true);
    setEditError('');
    try {
      await updateMessage(messageId, { subject: editSubject, body: editBody });
      await onChanged();
      setEditingMessageId(null);
    } catch {
      setEditError("Échec de l'enregistrement des modifications.");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleSend = async (messageId) => {
    setSendingId(messageId);
    setSendError('');
    try {
      await sendMessage(messageId);
      onChanged();
    } catch (error) {
      setSendError(error.response?.data?.detail || "Échec de l'envoi du message.");
    } finally {
      setSendingId(null);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${lead.first_name} ${lead.last_name}`.trim() || lead.email}
      subtitle="Détail du prospect"
      widthClass="max-w-2xl"
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={lead.status} label={lead.status_display} />
          {campaignName && (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
              {campaignName}
            </span>
          )}
          {lead.unsubscribed && (
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2.5 py-1 text-xs font-medium text-white">
              <BellOff className="h-3 w-3" /> Désinscrit
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-4 sm:grid-cols-2">
          <InfoRow icon={Mail} label="Email" value={lead.email} />
          <InfoRow icon={Phone} label="Téléphone" value={lead.phone} />
          <InfoRow icon={Building2} label="Entreprise" value={lead.company} />
          <InfoRow icon={Briefcase} label="Poste" value={lead.job_title} />
          <InfoRow icon={LinkIcon} label="LinkedIn" value={lead.linkedin_url} link />
          <InfoRow icon={LinkIcon} label="Site web" value={lead.website} link />
        </div>

        {lead.notes && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Notes</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{lead.notes}</p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Messages ({lead.messages?.length || 0})
            </p>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
              {generating ? 'Génération en cours...' : 'Générer un message IA'}
            </button>
          </div>

          {generateTimedOut && (
            <p className="mt-2 flex items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              La génération prend plus de temps que prévu. Elle est peut-être toujours en cours — réessaie de
              rouvrir cette fiche dans quelques instants.
            </p>
          )}

          {sendError && (
            <p className="mt-2 flex items-center gap-1.5 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {sendError}
            </p>
          )}

          <div className="mt-2 max-h-64 space-y-2 overflow-y-auto thin-scrollbar">
            {(!lead.messages || lead.messages.length === 0) && (
              <p className="rounded-lg bg-slate-50 px-3 py-4 text-center text-sm text-slate-400">
                Aucun message généré pour ce prospect.
              </p>
            )}
            {lead.messages?.map((msg) => {
              const canSend = ['DRAFT', 'FAILED'].includes(msg.status) && !lead.unsubscribed;
              const isEditing = editingMessageId === msg.id;

              if (isEditing) {
                return (
                  <div key={msg.id} className="rounded-lg border border-brand-200 bg-brand-50/30 p-3">
                    <input
                      value={editSubject}
                      onChange={(e) => setEditSubject(e.target.value)}
                      placeholder="Objet"
                      className="w-full rounded-md border border-slate-200 px-2 py-1 text-sm font-semibold text-slate-800 focus:border-brand-400 focus:outline-none"
                    />
                    <textarea
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      rows={6}
                      className="mt-2 w-full rounded-md border border-slate-200 px-2 py-1.5 text-xs text-slate-600 focus:border-brand-400 focus:outline-none"
                    />
                    {editError && <p className="mt-1.5 text-xs text-red-600">{editError}</p>}
                    <div className="mt-2 flex items-center gap-2">
                      <button
                        onClick={() => handleSaveEdit(msg.id)}
                        disabled={savingEdit}
                        className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                      >
                        {savingEdit && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                        Enregistrer
                      </button>
                      <button
                        onClick={cancelEdit}
                        disabled={savingEdit}
                        className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
                      >
                        Annuler
                      </button>
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="rounded-lg border border-slate-100 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{msg.subject || '(sans objet)'}</p>
                    <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                      {MESSAGE_STATUS_LABEL[msg.status] || msg.status}
                    </span>
                  </div>
                  <p className="mt-1 whitespace-pre-wrap text-xs text-slate-500">{msg.body}</p>
                  {canSend && (
                    <div className="mt-2 flex items-center gap-2">
                      <button
                        onClick={() => startEdit(msg)}
                        className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                      >
                        <Pencil className="h-3.5 w-3.5" /> Modifier
                      </button>
                      <button
                        onClick={() => handleSend(msg.id)}
                        disabled={sendingId === msg.id}
                        className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-60"
                      >
                        {sendingId === msg.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Send className="h-3.5 w-3.5" />
                        )}
                        {msg.status === 'FAILED' ? "Réessayer l'envoi" : 'Envoyer par email'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 pt-4">
          {confirmDelete ? (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-slate-600">Confirmer la suppression ?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-60"
              >
                {deleting ? 'Suppression...' : 'Oui, supprimer'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                Annuler
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="flex items-center gap-1.5 text-sm font-medium text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" /> Supprimer
            </button>
          )}

          <button
            onClick={() => onEdit(lead)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            <Pencil className="h-4 w-4" /> Modifier
          </button>
        </div>
      </div>
    </Modal>
  );
}

function InfoRow({ icon: Icon, label, value, link }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
      <div className="min-w-0">
        <p className="text-[11px] text-slate-400">{label}</p>
        {link ? (
          <a
            href={value}
            target="_blank"
            rel="noreferrer"
            className="truncate text-sm text-brand-600 hover:underline"
          >
            {value}
          </a>
        ) : (
          <p className="truncate text-sm text-slate-700">{value}</p>
        )}
      </div>
    </div>
  );
}
