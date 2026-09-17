import React from 'react';
import { ProjectListItem } from '../types';
import { AlertTriangle, Eye, Activity, CheckCircle2 } from 'lucide-react';

interface RealityGapViewProps {
  projects: ProjectListItem[];
  onSelectProject: (id: string) => void;
}

export const RealityGapView: React.FC<RealityGapViewProps> = ({ projects, onSelectProject }) => {
  // Sort projects by reality gap descending
  const sortedProjects = [...projects].sort((a, b) => (b.reality_gap_score ?? 0) - (a.reality_gap_score ?? 0));

  return (
    <div className="space-y-6">
      <div className="bg-command-panel border border-command-border rounded-xl p-5">
        <div className="flex items-center space-x-2 text-white font-semibold text-base mb-1">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <span>Reality Gap Analytical Monitor</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          The Reality Gap quantifies statistical and empirical divergence between contractor reported claims and ground reality evidence.
          Scores are scaled from 0-30 (NORMAL), 31-60 (WATCH), 61-80 (HIGH), 81-100 (CRITICAL).
        </p>
        <div className="mt-2 text-[11px] text-amber-300 font-medium">
          "This is a prototype/system-defined analytical score and is not an official government metric."
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sortedProjects.map((p) => {
          const gap = p.reality_gap_score ?? 0;
          const hasObserved = p.observed_progress !== null && p.observed_progress !== undefined;
          const rep = p.reported_progress;
          const obs = p.observed_progress;

          return (
            <div
              key={p.project_id}
              className="bg-command-panel border border-command-border rounded-xl p-5 flex flex-col justify-between space-y-4 hover:border-slate-600 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs text-command-cyan font-bold">{p.project_id}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    gap > 40 ? 'bg-rose-950 text-rose-300 border-rose-800' :
                    gap > 20 ? 'bg-amber-950 text-amber-300 border-amber-800' :
                    'bg-emerald-950 text-emerald-300 border-emerald-800'
                  }`}>
                    GAP SCORE: {gap.toFixed(1)}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white mb-2 line-clamp-1">{p.project_name}</h3>
                <p className="text-xs text-slate-400 mb-3">{p.district}, {p.state} | {p.project_type}</p>

                {/* Visual Gap Comparison Bars */}
                <div className="space-y-2.5 bg-command-dark p-3 rounded-lg border border-command-border/60 text-xs">
                  <div>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-slate-400">Reported Progress</span>
                      <span className="font-mono font-bold text-cyan-400">{rep.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${rep}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-slate-400">Observed Progress</span>
                      {hasObserved ? (
                        <span className="font-mono font-bold text-emerald-400">{obs?.toFixed(0)}%</span>
                      ) : (
                        <span className="text-[10px] text-amber-400 italic">DATA NOT AVAILABLE</span>
                      )}
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      {hasObserved ? (
                        <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${obs}%` }} />
                      ) : (
                        <div className="bg-slate-700 h-1.5 rounded-full opacity-30" style={{ width: '100%' }} />
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-command-border/60 flex items-center justify-between">
                <span className="text-[11px] text-slate-500">
                  {p.data_availability_status === 'SYNTHETIC' ? 'Synthetic Test Benchmark' : 'Government Ingested'}
                </span>
                <button
                  onClick={() => onSelectProject(p.project_id)}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-command-cyan transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Reality Gap</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
