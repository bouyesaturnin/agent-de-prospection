import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import Modal from './Modal';
import { createLead, updateLead } from '../api/client';

const EMPTY_FORM = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  company: '',
  job_title: '',
  linkedin_url: '',
  website: '',
  notes: '',
  campaign: '',
};

export default function LeadFormModal({ open, onClose, onSaved, campaigns, lead }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});

  const isEditing = Boolean(lead);

  useEffect(() => {
    if (open) {
      setForm(
        lead
          ? {
              first_name: lead.first_name || '',
              last_name: lead.last_name || '',
              email: lead.email || '',
              phone: lead.phone || '',
              company: lead.company || '',
              job_title: lead.job_title || '',
              linkedin_url: lead.linkedin_url || '',
              website: lead.website || '',
              notes: lead.notes || '',
              campaign: lead.campaign || '',
            }
          : EMPTY_FORM
      );
      setErrors({});
    }
  }, [open, lead]);

  const handleChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    const payload = { ...form, campaign: form.campaign || null };
    try {
      if (isEditing) {
        await updateLead(lead.id, payload);
      } else {
        await createLead(payload);
      }
      onSaved();
      onClose();
    } catch (error) {
      const data = error.response?.data;
      if (data && typeof data === 'object') {
        setErrors(data);
      } else {
        setErrors({ detail: "Une erreur est survenue lors de l'enregistrement." });
      }
    } finally {
      setSaving(false);
    }
  };

  const fieldError = (field) => errors[field] && (
    <p className="mt-1 text-xs text-red-600">{[].concat(errors[field]).join(' ')}</p>
  );

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Modifier le prospect' : 'Nouveau prospect'}
      subtitle={isEditing ? lead.email : 'Ajouter un prospect à la base'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.detail && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{errors.detail}</p>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-500">Prénom</label>
            <input
              type="text"
              value={form.first_name}
              onChange={handleChange('first_name')}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500">Nom</label>
            <input
              type="text"
              value={form.last_name}
              onChange={handleChange('last_name')}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Email *</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={handleChange('email')}
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
          {fieldError('email')}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-500">Entreprise</label>
            <input
              type="text"
              value={form.company}
              onChange={handleChange('company')}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500">Poste</label>
            <input
              type="text"
              value={form.job_title}
              onChange={handleChange('job_title')}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Campagne</label>
          <select
            value={form.campaign}
            onChange={handleChange('campaign')}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          >
            <option value="">Aucune</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Notes</label>
          <textarea
            rows={3}
            value={form.notes}
            onChange={handleChange('notes')}
            className="mt-1 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
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
            {isEditing ? 'Enregistrer' : 'Créer le prospect'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
