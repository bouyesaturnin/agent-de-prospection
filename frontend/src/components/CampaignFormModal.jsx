import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import Modal from './Modal';
import { createCampaign, updateCampaign } from '../api/client';

const EMPTY_FORM = {
  name: '',
  description: '',
  ai_prompt_template: '',
  followup_delay_days: 3,
  max_followups: 2,
};

export default function CampaignFormModal({ open, onClose, onSaved, campaign }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const isEditing = Boolean(campaign);

  useEffect(() => {
    if (open) {
      setForm(
        campaign
          ? {
              name: campaign.name || '',
              description: campaign.description || '',
              ai_prompt_template: campaign.ai_prompt_template || '',
              followup_delay_days: campaign.followup_delay_days ?? 3,
              max_followups: campaign.max_followups ?? 2,
            }
          : EMPTY_FORM
      );
      setError('');
    }
  }, [open, campaign]);

  const handleChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const handleNumberChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: Math.max(0, parseInt(e.target.value, 10) || 0) }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (isEditing) {
        await updateCampaign(campaign.id, form);
      } else {
        await createCampaign(form);
      }
      onSaved();
      onClose();
    } catch {
      setError("Impossible d'enregistrer la campagne.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Modifier la campagne' : 'Nouvelle campagne'}
      subtitle="Une campagne regroupe des prospects et un prompt IA dédié"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div>
          <label className="text-xs font-medium text-slate-500">Nom de la campagne *</label>
          <input
            required
            value={form.name}
            onChange={handleChange('name')}
            placeholder="Ex : Prospection SaaS RH — Q4 2026"
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Description / Objectif</label>
          <textarea
            rows={2}
            value={form.description}
            onChange={handleChange('description')}
            className="mt-1 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Prompt IA spécifique</label>
          <textarea
            rows={4}
            value={form.ai_prompt_template}
            onChange={handleChange('ai_prompt_template')}
            placeholder="Ex : Ton ton doit être direct et orienté ROI. Mets en avant notre offre d'audit gratuit..."
            className="mt-1 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
          <p className="mt-1 text-xs text-slate-400">
            Ces instructions sont injectées dans le prompt Claude lors de la génération des messages pour les
            prospects de cette campagne.
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
          <p className="text-xs font-semibold text-slate-600">Relances automatiques</p>
          <p className="mt-0.5 text-xs text-slate-400">
            Générées en brouillon uniquement — jamais envoyées sans ta validation.
          </p>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-500">Délai avant relance (jours)</label>
              <input
                type="number"
                min={0}
                value={form.followup_delay_days}
                onChange={handleNumberChange('followup_delay_days')}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500">Nombre max de relances</label>
              <input
                type="number"
                min={0}
                value={form.max_followups}
                onChange={handleNumberChange('max_followups')}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Annuler
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            {isEditing ? 'Enregistrer' : 'Créer la campagne'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
