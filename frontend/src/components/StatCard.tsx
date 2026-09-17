import React from 'react';

interface StatCardProps {
  label: string;
  value: number | string;
  subtext?: string;
  status?: 'normal' | 'warning' | 'critical' | 'neutral';
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subtext, status = 'neutral', icon }) => {
  const statusStyles = {
    normal: 'border-emerald-800/40 bg-emerald-950/20 text-emerald-400',
    warning: 'border-amber-800/40 bg-amber-950/20 text-amber-400',
    critical: 'border-rose-800/40 bg-rose-950/20 text-rose-400',
    neutral: 'border-command-border bg-command-panel/70 text-slate-300',
  };

  const badgeColor = {
    normal: 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60',
    warning: 'text-amber-400 bg-amber-950/60 border-amber-800/60',
    critical: 'text-rose-400 bg-rose-950/60 border-rose-800/60',
    neutral: 'text-slate-400 bg-slate-900 border-slate-700',
  };

  return (
    <div className={`p-4 rounded-xl border ${statusStyles[status]} flex flex-col justify-between shadow-sm transition-all hover:border-slate-600`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div>
        <div className="text-2xl font-bold font-mono tracking-tight text-white mb-1">
          {value}
        </div>
        {subtext && (
          <span className={`inline-block text-[10px] px-2 py-0.5 rounded border font-medium ${badgeColor[status]}`}>
            {subtext}
          </span>
        )}
      </div>
    </div>
  );
};
