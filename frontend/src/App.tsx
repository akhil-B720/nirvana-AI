import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { GisMap } from './components/GisMap';
import { ProjectList } from './components/ProjectList';
import { ProjectIntelligence } from './components/ProjectIntelligence';
import { RealityGapView } from './components/RealityGapView';
import { VerificationCasesView } from './components/VerificationCasesView';
import { ModelRegistryView } from './components/ModelRegistryView';
import { AssistantDrawer } from './components/AssistantDrawer';
import { EvidenceUploadModal } from './components/EvidenceUploadModal';
import { api } from './services/api';
import { ProjectListItem, ProjectDetail, AnalyticsOverview } from './types';
import {
  Layers, AlertTriangle, CheckCircle2, Clock, ShieldAlert,
  FileText, Activity, RefreshCw, ChevronLeft
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();
  const [selectedProjectDetail, setSelectedProjectDetail] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  // Load initial data from FastAPI backend
  const loadData = async () => {
    try {
      setLoading(true);
      const [overviewData, projectsData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getProjects()
      ]);
      setAnalytics(overviewData);
      setProjects(projectsData);
      if (projectsData.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projectsData[0].project_id);
      }
    } catch (err) {
      console.error('Failed to load NIRVANA platform data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Fetch detailed project intelligence when selected
  useEffect(() => {
    if (!selectedProjectId) return;
    api.getProjectDetail(selectedProjectId)
      .then((detail) => setSelectedProjectDetail(detail))
      .catch((err) => console.error('Failed to fetch project detail:', err));
  }, [selectedProjectId]);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenAssistant={() => setIsAssistantOpen(true)}
        onOpenUpload={() => setIsUploadOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* KPI Dashboard Metrics Row (Connected live to backend API) */}
        {analytics && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <StatCard
              label="Total Works"
              value={analytics.total_projects}
              subtext="Registered in Registry"
              status="neutral"
              icon={<FileText className="w-4 h-4 text-slate-400" />}
            />
            <StatCard
              label="Monitored"
              value={analytics.projects_monitored}
              subtext="Active AI Pipeline"
              status="normal"
              icon={<Activity className="w-4 h-4 text-emerald-400" />}
            />
            <StatCard
              label="High Risk"
              value={analytics.high_risk_projects}
              subtext="Review Advised"
              status={analytics.high_risk_projects > 0 ? 'warning' : 'normal'}
              icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
            />
            <StatCard
              label="Critical"
              value={analytics.critical_risk_projects}
              subtext="Priority Audit"
              status={analytics.critical_risk_projects > 0 ? 'critical' : 'normal'}
              icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
            />
            <StatCard
              label="Timeline Delayed"
              value={analytics.delayed_projects}
              subtext="S-Curve Slippage"
              status={analytics.delayed_projects > 0 ? 'warning' : 'normal'}
              icon={<Clock className="w-4 h-4 text-sky-400" />}
            />
            <StatCard
              label="Reality Gaps"
              value={analytics.active_reality_gaps}
              subtext="Reported ≠ Ground"
              status={analytics.active_reality_gaps > 0 ? 'critical' : 'normal'}
              icon={<Layers className="w-4 h-4 text-cyan-400" />}
            />
          </div>
        )}

        {/* Tab Views */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* GIS Map & Selected Intelligence Split View */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* GIS Map View */}
              <div className="lg:col-span-7 flex flex-col space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white tracking-wide uppercase flex items-center gap-2">
                    <Layers className="w-4 h-4 text-command-cyan" />
                    Geospatial Infrastructure Reality Map
                  </h3>
                  <span className="text-[11px] text-slate-400">
                    Showing {projects.length} Works
                  </span>
                </div>
                <GisMap
                  projects={projects}
                  selectedProjectId={selectedProjectId}
                  onSelectProject={(id) => setSelectedProjectId(id)}
                />
              </div>

              {/* Selected Project Intelligence Summary */}
              <div className="lg:col-span-5 flex flex-col space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white tracking-wide uppercase flex items-center gap-2">
                    <Activity className="w-4 h-4 text-command-cyan" />
                    Selected Asset Intelligence
                  </h3>
                  {selectedProjectId && (
                    <button
                      onClick={() => setActiveTab('projects')}
                      className="text-[11px] text-command-cyan hover:underline"
                    >
                      Full Dossier &rarr;
                    </button>
                  )}
                </div>

                {selectedProjectDetail ? (
                  <div className="bg-command-panel border border-command-border rounded-xl p-5 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-command-border/60">
                      <div>
                        <span className="font-mono text-xs text-command-cyan font-bold">{selectedProjectDetail.project_id}</span>
                        <h4 className="text-sm font-bold text-white line-clamp-1">{selectedProjectDetail.project_name}</h4>
                        <p className="text-[11px] text-slate-400">{selectedProjectDetail.district}, {selectedProjectDetail.state}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        selectedProjectDetail.risk_tier === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border-rose-800' :
                        selectedProjectDetail.risk_tier === 'HIGH' ? 'bg-orange-950 text-orange-300 border-orange-800' :
                        'bg-emerald-950 text-emerald-300 border-emerald-800'
                      }`}>
                        {selectedProjectDetail.risk_tier} ({selectedProjectDetail.fused_risk_score?.toFixed(0) ?? 0})
                      </span>
                    </div>

                    {/* Progress Metrics */}
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="bg-command-dark p-2.5 rounded border border-command-border/60">
                        <span className="text-slate-400 block text-[10px]">Reported Claim</span>
                        <span className="font-mono text-base font-bold text-cyan-400">{selectedProjectDetail.reported_progress.toFixed(0)}%</span>
                      </div>
                      <div className="bg-command-dark p-2.5 rounded border border-command-border/60">
                        <span className="text-slate-400 block text-[10px]">Observed Evidence</span>
                        {selectedProjectDetail.observed_progress !== null && selectedProjectDetail.observed_progress !== undefined ? (
                          <span className="font-mono text-base font-bold text-emerald-400">{selectedProjectDetail.observed_progress.toFixed(0)}%</span>
                        ) : (
                          <span className="text-[10px] text-amber-400 font-sans italic">DATA NOT AVAILABLE</span>
                        )}
                      </div>
                    </div>

                    {/* Contributing Factors */}
                    <div className="text-xs space-y-1">
                      <span className="text-slate-400 font-medium">Anomaly Triggers:</span>
                      {selectedProjectDetail.risk_summary?.contributing_factors && selectedProjectDetail.risk_summary.contributing_factors.length > 0 ? (
                        <ul className="list-disc list-inside text-slate-300 text-[11px] space-y-1">
                          {selectedProjectDetail.risk_summary.contributing_factors.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-slate-500 text-[11px] italic">No anomalies triggered.</p>
                      )}
                    </div>

                    {/* Button to open full detail */}
                    <button
                      onClick={() => setActiveTab('projects')}
                      className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition text-center block"
                    >
                      Open Comprehensive 3D Digital Twin & Audit
                    </button>
                  </div>
                ) : (
                  <div className="bg-command-panel border border-command-border rounded-xl p-8 text-center text-slate-500 text-xs">
                    Select a project point on the GIS map to inspect intelligence.
                  </div>
                )}
              </div>
            </div>

            {/* Project Registry Table */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wide">
                Sanctioned Public Works Registry
              </h3>
              <ProjectList
                projects={projects}
                selectedProjectId={selectedProjectId}
                onSelectProject={(id) => {
                  setSelectedProjectId(id);
                }}
              />
            </div>
          </div>
        )}

        {/* 3D GIS Map Dedicated Tab */}
        {activeTab === 'map' && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wide">
              Full-Screen Geospatial & Reality Plane Inspection
            </h3>
            <GisMap
              projects={projects}
              selectedProjectId={selectedProjectId}
              onSelectProject={(id) => {
                setSelectedProjectId(id);
                setActiveTab('projects');
              }}
            />
          </div>
        )}

        {/* Project Registry / Detail Deep Dive Tab */}
        {activeTab === 'projects' && (
          <div className="space-y-6">
            {selectedProjectDetail ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setSelectedProjectId(undefined)}
                    className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-white"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Back to Registry Table</span>
                  </button>
                </div>
                <ProjectIntelligence
                  project={selectedProjectDetail}
                  onRefresh={loadData}
                />
              </div>
            ) : (
              <ProjectList
                projects={projects}
                selectedProjectId={selectedProjectId}
                onSelectProject={(id) => setSelectedProjectId(id)}
              />
            )}
          </div>
        )}

        {/* Reality Gap Tab */}
        {activeTab === 'reality-gap' && (
          <RealityGapView
            projects={projects}
            onSelectProject={(id) => {
              setSelectedProjectId(id);
              setActiveTab('projects');
            }}
          />
        )}

        {/* Verification Cases Tab */}
        {activeTab === 'cases' && <VerificationCasesView />}

        {/* Model Registry Tab */}
        {activeTab === 'models' && <ModelRegistryView />}
      </main>

      {/* Slide-over Contextual AI Assistant */}
      <AssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        selectedProjectId={selectedProjectId}
      />

      {/* Field Evidence Upload Modal */}
      <EvidenceUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        projects={projects}
        onUploadSuccess={loadData}
      />

      {/* Statutory Footer */}
      <footer className="border-t border-command-border bg-command-dark py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>NIRVANA | Team TYRANTS | Smart India Hackathon SIH26102</span>
          <span className="text-[11px] text-slate-400">
            "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing."
          </span>
        </div>
      </footer>
    </div>
  );
};
