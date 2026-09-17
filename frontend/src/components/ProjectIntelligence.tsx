import React from 'react';
import { ProjectDetail } from '../types';
import { DigitalTwin3D } from './DigitalTwin3D';
import { api } from '../services/api';
import {
  FileText, Download, AlertTriangle, CheckCircle, Clock,
  DollarSign, Activity, Compass, ShieldAlert, ChevronRight, HelpCircle
} from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface ProjectIntelligenceProps {
  project: ProjectDetail;
  onRefresh: () => void;
}

export const ProjectIntelligence: React.FC<ProjectIntelligenceProps> = ({ project, onRefresh }) => {
  const rg = project.reality_gap_summary;
  const risk = project.risk_summary;

  // Radar DNA Data
  const hasObserved = project.observed_progress !== null && project.observed_progress !== undefined;
  const radarData = [
    { subject: 'Financial Util', value: Math.min(100, (project.expenditure_amount / Math.max(1, project.released_amount)) * 100) },
    { subject: 'Reported Prog', value: project.reported_progress },
    { subject: 'Observed Prog', value: hasObserved ? (project.observed_progress ?? 0) : 0 },
    { subject: 'Timeline Exp', value: Math.min(100, (rg?.time_elapsed_ratio ?? 0.5) * 100) },
    { subject: 'Risk Intensity', value: risk?.fused_risk_score ?? 0 },
  ];

  // Financial S-Curve Comparison Data
  const finData = [
    { stage: 'Sanction', amount: project.sanction_amount / 100000 },
    { stage: 'Released', amount: project.released_amount / 100000 },
    { stage: 'Expended', amount: project.expenditure_amount / 100000 },
  ];

  const handleDownloadReport = () => {
    window.open(api.getReportUrl(project.project_id), '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-command-panel border border-command-border rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-command-cyan font-bold border border-slate-700">
              {project.project_id}
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
              {project.project_type}
            </span>
            {project.data_availability_status === 'SYNTHETIC' && (
              <span className="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-bold">
                SYNTHETIC RECORD
              </span>
            )}
            <span className="text-xs text-slate-400 font-medium">
              {project.district}, {project.state}
            </span>
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">{project.project_name}</h2>
          <p className="text-xs text-slate-400 mt-1">
            Agency: <span className="text-slate-200">{project.agency || 'Unspecified Executive Agency'}</span> | Sector: <span className="text-slate-200">{project.sector || 'General Infrastructure'}</span>
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleDownloadReport}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow transition"
          >
            <Download className="w-4 h-4" />
            <span>Export PDF Dossier</span>
          </button>
        </div>
      </div>

      {/* 3D Digital Twin Section */}
      <DigitalTwin3D
        projectType={project.project_type}
        reportedProgress={project.reported_progress}
        observedProgress={project.observed_progress}
        expectedProgress={rg?.expected_progress}
        projectName={project.project_name}
      />

      {/* Reality Planes Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Expected Plane */}
        <div className="bg-command-panel border border-command-border rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Expected Reality</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mb-1">
            {rg?.expected_progress !== null && rg?.expected_progress !== undefined ? `${rg.expected_progress.toFixed(1)}%` : 'DATA NOT AVAILABLE'}
          </div>
          <p className="text-[11px] text-slate-400">
            Algorithmic S-curve milestone from sanctioned project duration.
          </p>
        </div>

        {/* Reported Plane */}
        <div className="bg-command-panel border border-command-border rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Reported Reality</span>
            <FileText className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mb-1">
            {project.reported_progress.toFixed(1)}%
          </div>
          <p className="text-[11px] text-slate-400">
            Administrative claim submitted by implementing contractor.
          </p>
        </div>

        {/* Observed Plane */}
        <div className="bg-command-panel border border-command-border rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Observed Reality</span>
            <Compass className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mb-1">
            {hasObserved ? (
              <span className="text-emerald-400">{project.observed_progress?.toFixed(1)}%</span>
            ) : (
              <span className="text-sm font-sans text-amber-400">DATA NOT AVAILABLE</span>
            )}
          </div>
          <p className="text-[11px] text-slate-400">
            {hasObserved ? 'Verified from geotagged field survey photography.' : 'No verified field inspection photo on record.'}
          </p>
        </div>
      </div>

      {/* AI Explanation & Anomaly Chain */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grounded AI Explanation */}
        <div className="bg-command-panel border border-command-border rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-white font-semibold text-sm mb-3">
              <ShieldAlert className="w-4 h-4 text-command-cyan" />
              <span>Grounded Analytical Risk Explanation</span>
            </div>

            <div className="bg-command-dark p-3.5 rounded-lg border border-command-border text-xs space-y-2">
              <p className="text-slate-300 font-medium">
                Primary Contributing Factors Identified:
              </p>
              {risk?.contributing_factors && risk.contributing_factors.length > 0 ? (
                <ul className="space-y-1.5 text-slate-400 list-disc list-inside">
                  {risk.contributing_factors.map((factor, idx) => (
                    <li key={idx} className="leading-relaxed text-slate-300">{factor}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400 italic">No significant anomalies or deviations flagged for this work.</p>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-command-border text-[11px] text-amber-300/80 italic">
            "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
          </div>
        </div>

        {/* Project DNA Radar Visual */}
        <div className="bg-command-panel border border-command-border rounded-xl p-5">
          <div className="flex items-center justify-between text-white font-semibold text-sm mb-2">
            <span className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-command-cyan" />
              <span>Project Analytical DNA</span>
            </span>
            <span className="text-[11px] text-slate-400">Multi-axis alignment</span>
          </div>

          <div className="w-full h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Radar name="Project DNA" dataKey="value" stroke="#38bdf8" fill="#0284c7" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Verification Recommendations Checklist */}
      <div className="bg-command-panel border border-command-border rounded-xl p-5">
        <div className="flex items-center space-x-2 text-white font-semibold text-sm mb-3">
          <CheckCircle className="w-4 h-4 text-command-cyan" />
          <span>Prescribed Verification Recommendations (Traceable Triggers)</span>
        </div>

        <div className="space-y-2.5">
          {project.recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="p-3 bg-command-dark rounded-lg border border-command-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    rec.priority === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border-rose-800' :
                    rec.priority === 'HIGH' ? 'bg-orange-950 text-orange-300 border-orange-800' :
                    'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {rec.priority}
                  </span>
                  <span className="font-semibold text-slate-200">{rec.trigger}</span>
                </div>
                <p className="text-slate-400 text-[11px] pl-0.5">{rec.recommended_action}</p>
              </div>

              <span className="font-mono text-[10px] px-2 py-1 rounded bg-slate-800 text-command-cyan border border-slate-700 whitespace-nowrap">
                {rec.action_type}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
