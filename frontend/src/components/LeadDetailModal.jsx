import { useState } from 'react';
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
import { deleteLead, generateAiMessage, sendMessage } from '../api/client';

const MESSAGE_STATUS_LABEL = {
  DRAFT: 'Brouillon',
  QUEUED: "En attente d'envoi",
  SENT: 'Envoyé',
  FAILED: 'Échec',
  RECEIVED: 'Réponse reçue',
};

export default function LeadDetailModal({ open, onClose, lead, campaignName, onEdit, onChanged }) {
  const [deleting, setDeleting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [sendingId, setSendingId] = useState(null);
  const [sendError, setSendError] = useState('');

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
    setGenerating(true);
    try {
      await generateAiMessage(lead.id);
      onChanged();
    } finally {
      setGenerating(false);
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
              Générer un message IA
            </button>
          </div>

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
                    <button
                      onClick={() => handleSend(msg.id)}
                      disabled={sendingId === msg.id}
                      className="mt-2 flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-60"
                    >
                      {sendingId === msg.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Send className="h-3.5 w-3.5" />
                      )}
                      {msg.status === 'FAILED' ? "Réessayer l'envoi" : 'Envoyer par email'}
                    </button>
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
