import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ModelRegistryItem } from '../types';
import { Cpu, CheckCircle, AlertTriangle, Clock, Database, Layers } from 'lucide-react';

export const ModelRegistryView: React.FC = () => {
  const [models, setModels] = useState<ModelRegistryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getModels()
      .then((data) => setModels(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-command-panel border border-command-border rounded-xl p-5">
        <div className="flex items-center space-x-2 text-white font-semibold text-base mb-1">
          <Cpu className="w-5 h-5 text-command-cyan" />
          <span>NIRVANA Operational Model Registry & Governance Audit</span>
        </div>
        <p className="text-xs text-slate-400">
          All analytical detectors, anomaly estimators, and computer vision interfaces are tracked under strict version control.
          Models without ground-truth labels remain strictly categorized as baseline heuristics or NOT_TRAINED.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((m) => (
          <div key={m.model_id} className="bg-command-panel border border-command-border rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-command-cyan font-bold">{m.model_id}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  m.status === 'ACTIVE' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' :
                  m.status === 'INSUFFICIENT_DATA' ? 'bg-amber-950 text-amber-300 border-amber-800' :
                  'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {m.status}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white mb-1">{m.model_name} (v{m.version})</h3>
              <p className="text-xs text-slate-300 font-mono text-[11px] mb-3">Algorithm: {m.algorithm}</p>

              <div className="bg-command-dark p-3 rounded-lg border border-command-border/60 text-xs space-y-1.5 font-mono text-[11px]">
                <div className="text-slate-400">Training Data Version: <span className="text-slate-200">{m.training_data_version}</span></div>
                {m.training_timestamp && (
                  <div className="text-slate-400">Trained At: <span className="text-slate-200">{new Date(m.training_timestamp).toLocaleString()}</span></div>
                )}
                <div className="pt-2 border-t border-command-border/40 text-slate-300">
                  <div className="text-slate-400 font-sans text-xs mb-1">Evaluated Metrics / Parameters:</div>
                  <pre className="text-[10px] text-command-cyan overflow-x-auto p-1.5 bg-slate-900 rounded">
                    {JSON.stringify(m.metrics, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 italic">
              Governed by NIRVANA Responsible AI Policy & Data Integrity Standard.
            </div>
          </div>
        ))}

        {/* Physical Progress Computer Vision Interface Card */}
        <div className="bg-command-panel border border-command-border rounded-xl p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-command-cyan font-bold">cv_physical_progress_v1</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-slate-800 text-slate-400 border-slate-700">
                MODEL_NOT_TRAINED
              </span>
            </div>
            <h3 className="text-sm font-bold text-white mb-1">PhysicalProgressEstimator (Interface)</h3>
            <p className="text-xs text-slate-300 font-mono text-[11px] mb-3">Architecture: YOLO / ResNet Multi-Milestone Detector</p>

            <div className="bg-command-dark p-3 rounded-lg border border-command-border/60 text-xs space-y-2 text-slate-300">
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Targeted structural classes: Foundation, Columns, Beams, Masonry Walls, Roof Slab, Asphalt, Markings, Water Tank dome.
              </p>
              <div className="p-2 bg-amber-950/40 border border-amber-800/40 rounded text-[11px] text-amber-200">
                <strong>Ground-Truth Transparency:</strong> Awaiting mounting of domain-specific annotated construction drone/ground dataset. Fake accuracy numbers are strictly prohibited.
              </div>
            </div>
          </div>

          <div className="text-[11px] text-slate-500 italic">
            Physical evidence is reported as null with status NOT_AVAILABLE until verified.
          </div>
        </div>
      </div>
    </div>
  );
};
