import React, { useState, useMemo } from 'react';
import { ProjectListItem } from '../types';
import { Search, Filter, AlertTriangle, ArrowUpDown, ChevronRight, Eye } from 'lucide-react';

interface ProjectListProps {
  projects: ProjectListItem[];
  selectedProjectId?: string;
  onSelectProject: (projectId: string) => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({ projects, selectedProjectId, onSelectProject }) => {
  const [search, setSearch] = useState('');
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchSearch =
        p.project_name.toLowerCase().includes(search.toLowerCase()) ||
        p.project_id.toLowerCase().includes(search.toLowerCase()) ||
        p.district.toLowerCase().includes(search.toLowerCase());
      const matchTier = selectedTier === 'ALL' || p.risk_tier === selectedTier;
      const matchType = selectedType === 'ALL' || p.project_type === selectedType;
      return matchSearch && matchTier && matchType;
    });
  }, [projects, search, selectedTier, selectedType]);

  const riskBadgeStyles = {
    CRITICAL: 'bg-rose-950/80 text-rose-300 border-rose-800',
    HIGH: 'bg-orange-950/80 text-orange-300 border-orange-800',
    WATCH: 'bg-amber-950/80 text-amber-300 border-amber-800',
    NORMAL: 'bg-emerald-950/80 text-emerald-300 border-emerald-800',
  };

  return (
    <div className="bg-command-panel border border-command-border rounded-xl p-4 flex flex-col space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by project ID, title, district..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-command-dark border border-command-border rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-command-cyan"
            aria-label="Search projects"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Risk Tier Filter */}
          <select
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-command-dark border border-command-border rounded-lg text-slate-300 focus:outline-none"
            aria-label="Filter by risk tier"
          >
            <option value="ALL">All Risk Tiers</option>
            <option value="NORMAL">Normal</option>
            <option value="WATCH">Watch</option>
            <option value="HIGH">High Risk</option>
            <option value="CRITICAL">Critical</option>
          </select>

          {/* Project Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-command-dark border border-command-border rounded-lg text-slate-300 focus:outline-none"
            aria-label="Filter by project type"
          >
            <option value="ALL">All Project Types</option>
            <option value="BUILDING">Building</option>
            <option value="ROAD">Road</option>
            <option value="BRIDGE">Bridge</option>
            <option value="WATER_TANK">Water Tank</option>
          </select>
        </div>
      </div>

      {/* Projects Table */}
      <div className="overflow-x-auto border border-command-border/60 rounded-lg">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-command-dark/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-command-border/80">
            <tr>
              <th className="py-2.5 px-3">Project ID</th>
              <th className="py-2.5 px-3">Name & Type</th>
              <th className="py-2.5 px-3">Location</th>
              <th className="py-2.5 px-3">Sanction (₹)</th>
              <th className="py-2.5 px-3">Reported</th>
              <th className="py-2.5 px-3">Observed</th>
              <th className="py-2.5 px-3">Risk Tier</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-command-border/40 font-mono">
            {filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                  No projects match the specified filter criteria.
                </td>
              </tr>
            ) : (
              filteredProjects.map((p) => {
                const isSelected = p.project_id === selectedProjectId;
                const tier = p.risk_tier || 'NORMAL';
                const hasObserved = p.observed_progress !== null && p.observed_progress !== undefined;

                return (
                  <tr
                    key={p.project_id}
                    onClick={() => onSelectProject(p.project_id)}
                    className={`cursor-pointer transition-colors hover:bg-slate-800/40 ${
                      isSelected ? 'bg-command-accent/15 border-l-4 border-command-cyan' : ''
                    }`}
                  >
                    <td className="py-3 px-3 font-semibold text-command-cyan whitespace-nowrap">
                      {p.project_id}
                      {p.data_availability_status === 'SYNTHETIC' && (
                        <span className="block text-[9px] text-amber-400 font-sans mt-0.5">SYNTHETIC FIXTURE</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-sans max-w-xs truncate">
                      <span className="text-white font-medium block truncate">{p.project_name}</span>
                      <span className="text-[10px] text-slate-400 font-mono uppercase">{p.project_type}</span>
                    </td>
                    <td className="py-3 px-3 font-sans whitespace-nowrap">
                      <span className="text-slate-200">{p.district}</span>
                      <span className="block text-[10px] text-slate-500">{p.state}</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-200 whitespace-nowrap">
                      ₹{p.sanction_amount.toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-200">
                      {p.reported_progress.toFixed(0)}%
                    </td>
                    <td className="py-3 px-3 font-mono">
                      {hasObserved ? (
                        <span className="text-emerald-400 font-bold">{p.observed_progress?.toFixed(0)}%</span>
                      ) : (
                        <span className="text-[10px] text-slate-500 font-sans italic">DATA NOT AVAILABLE</span>
                      )}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${riskBadgeStyles[tier]}`}>
                        {tier} ({p.fused_risk_score?.toFixed(0) ?? 0})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectProject(p.project_id);
                        }}
                        className="inline-flex items-center space-x-1 px-2 py-1 text-[11px] font-sans font-medium rounded bg-slate-800 hover:bg-slate-700 text-command-cyan transition"
                        aria-label={`Inspect project ${p.project_id}`}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
