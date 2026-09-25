import { useState } from 'react';
import { Loader2, UploadCloud, CheckCircle2 } from 'lucide-react';
import Modal from './Modal';
import { importLeadsCsv } from '../api/client';

export default function ImportCsvModal({ open, onClose, onImported, campaigns }) {
  const [file, setFile] = useState(null);
  const [campaignId, setCampaignId] = useState('');
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const reset = () => {
    setFile(null);
    setCampaignId('');
    setResult(null);
    setError('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setImporting(true);
    setError('');
    setResult(null);
    try {
      const response = await importLeadsCsv(file, campaignId || null);
      setResult(response.data);
      onImported();
    } catch (err) {
      setError(err.response?.data?.detail || "Échec de l'import du fichier CSV.");
    } finally {
      setImporting(false);
    }
  };

  return (
    <Modal open={open} onClose={handleClose} title="Importer des prospects" subtitle="Fichier CSV avec une colonne 'email' obligatoire">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-slate-500">Fichier CSV</label>
          <label className="mt-1 flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed border-slate-200 px-4 py-8 text-center transition hover:border-brand-300 hover:bg-brand-50/30">
            <UploadCloud className="h-8 w-8 text-slate-300" />
            <span className="text-sm font-medium text-slate-600">
              {file ? file.name : 'Cliquer pour sélectionner un fichier .csv'}
            </span>
            <span className="text-xs text-slate-400">
              Colonnes reconnues : email, first_name, last_name, phone, company, job_title, linkedin_url, website, notes
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">Assigner à une campagne (optionnel)</label>
          <select
            value={campaignId}
            onChange={(e) => setCampaignId(e.target.value)}
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

        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        {result && (
          <div className="flex items-start gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p>
                {result.created} prospect(s) importé(s), {result.skipped} doublon(s) ignoré(s).
              </p>
              {result.errors?.length > 0 && (
                <ul className="mt-1 list-disc pl-4 text-xs text-amber-700">
                  {result.errors.slice(0, 5).map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Fermer
          </button>
          <button
            type="submit"
            disabled={!file || importing}
            className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {importing && <Loader2 className="h-4 w-4 animate-spin" />}
            Importer
          </button>
        </div>
      </form>
    </Modal>
  );
}
