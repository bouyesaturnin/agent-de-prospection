import { Info, AlertTriangle, XCircle } from 'lucide-react';

const LEVEL_CONFIG = {
  INFO: { icon: Info, badge: 'bg-blue-100', text: 'text-blue-700' },
  WARNING: { icon: AlertTriangle, badge: 'bg-amber-100', text: 'text-amber-700' },
  ERROR: { icon: XCircle, badge: 'bg-red-100', text: 'text-red-700' },
};

function timeAgo(isoDate) {
  const diffMs = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `il y a ${hours} h`;
  const days = Math.floor(hours / 24);
  return `il y a ${days} j`;
}

export default function ActivityFeed({ logs, loading }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-900">Activité récente</h2>
      <p className="mt-0.5 text-xs text-slate-400">Journal des actions de l'agent</p>

      <div className="thin-scrollbar mt-4 max-h-96 space-y-4 overflow-y-auto pr-1">
        {loading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-100" />
          ))
        ) : logs.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-400">Aucune activité pour le moment.</p>
        ) : (
          logs.map((log) => {
            const config = LEVEL_CONFIG[log.level] || LEVEL_CONFIG.INFO;
            const Icon = config.icon;
            return (
              <div key={log.id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-full ${config.badge}`}>
                    <Icon className={`h-3.5 w-3.5 ${config.text}`} />
                  </span>
                  <span className="mt-1 h-full w-px bg-slate-100" />
                </div>
                <div className="min-w-0 pb-1">
                  <p className="text-sm font-medium text-slate-800">{log.action}</p>
                  <p className="mt-0.5 truncate text-xs text-slate-500" title={log.message}>
                    {log.message}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-400">{timeAgo(log.timestamp)}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
