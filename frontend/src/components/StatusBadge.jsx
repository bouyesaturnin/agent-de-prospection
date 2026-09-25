const LEAD_STATUS_STYLES = {
  NEW: 'bg-slate-100 text-slate-600 ring-slate-200',
  GENERATED: 'bg-blue-50 text-blue-700 ring-blue-200',
  CONTACTED: 'bg-amber-50 text-amber-700 ring-amber-200',
  REPLIED: 'bg-purple-50 text-purple-700 ring-purple-200',
  QUALIFIED: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  UNQUALIFIED: 'bg-rose-50 text-rose-700 ring-rose-200',
  BOUNCED: 'bg-red-50 text-red-700 ring-red-200',
};

export default function StatusBadge({ status, label }) {
  const styles = LEAD_STATUS_STYLES[status] || LEAD_STATUS_STYLES.NEW;
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styles}`}
    >
      {label || status}
    </span>
  );
}
