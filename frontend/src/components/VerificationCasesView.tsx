import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { VerificationCase } from '../types';
import { CheckCircle2, AlertTriangle, Shield, Clock, FileCheck } from 'lucide-react';

export const VerificationCasesView: React.FC = () => {
  const [cases, setCases] = useState<VerificationCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getVerificationCases()
      .then((data) => setCases(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-command-panel border border-command-border rounded-xl p-5">
        <div className="flex items-center space-x-2 text-white font-semibold text-base mb-1">
          <CheckCircle2 className="w-5 h-5 text-command-cyan" />
          <span>Human-in-the-Loop Verification Triage & Field Case Registry</span>
        </div>
        <p className="text-xs text-slate-400">
          AI triggers decision-support anomaly signals. Nodal officers and authorized vigilance engineers perform final ground audits.
        </p>
      </div>

      <div className="bg-command-panel border border-command-border rounded-xl p-4 overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-command-dark text-slate-400 uppercase tracking-wider font-semibold border-b border-command-border">
            <tr>
              <th className="py-2.5 px-3">Case ID</th>
              <th className="py-2.5 px-3">Project</th>
              <th className="py-2.5 px-3">Priority</th>
              <th className="py-2.5 px-3">Trigger Reason</th>
              <th className="py-2.5 px-3">Prescribed Action</th>
              <th className="py-2.5 px-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-command-border/40">
            {cases.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No active verification cases found. Cases are generated dynamically from detected reality gaps.
                </td>
              </tr>
            ) : (
              cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 font-mono font-bold text-command-cyan whitespace-nowrap">{c.case_id}</td>
                  <td className="py-3 px-3 max-w-xs truncate">
                    <span className="text-white font-medium block truncate">{c.project_name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{c.project_id}</span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      c.priority === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border-rose-800' :
                      c.priority === 'HIGH' ? 'bg-orange-950 text-orange-300 border-orange-800' :
                      'bg-slate-800 text-slate-300 border-slate-700'
                    }`}>
                      {c.priority}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300 leading-relaxed">{c.trigger_reason}</td>
                  <td className="py-3 px-3 text-slate-400 leading-relaxed">{c.recommended_action}</td>
                  <td className="py-3 px-3 whitespace-nowrap font-mono font-bold">
                    <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[10px]">
                      {c.case_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
