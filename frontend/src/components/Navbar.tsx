import React from 'react';
import { Shield, MapPin, Eye, AlertTriangle, Cpu, FileText, CheckCircle2, MessageSquare, Upload } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenAssistant: () => void;
  onOpenUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onOpenAssistant, onOpenUpload }) => {
  const navItems = [
    { id: 'overview', label: 'Command Center', icon: Eye },
    { id: 'map', label: 'GIS & 3D Map', icon: MapPin },
    { id: 'projects', label: 'Project Registry', icon: FileText },
    { id: 'reality-gap', label: 'Reality Gap', icon: AlertTriangle },
    { id: 'cases', label: 'Verification Cases', icon: CheckCircle2 },
    { id: 'models', label: 'Model Registry', icon: Cpu },
  ];

  return (
    <header className="border-b border-command-border bg-command-dark/95 backdrop-blur sticky top-0 z-40">
      {/* Top Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-command-accent/10 border border-command-accent/30 rounded-lg text-command-cyan">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-wider text-white">NIRVANA</span>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-800 rounded">
                  SIH26102
                </span>
                <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-800 text-slate-300 rounded">
                  TEAM TYRANTS
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium truncate max-w-md hidden sm:block">
                National Infrastructure Reality & Verification Network using AI
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={onOpenUpload}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              aria-label="Upload field evidence"
            >
              <Upload className="w-3.5 h-3.5 text-command-cyan" />
              <span>Upload Evidence</span>
            </button>
            <button
              onClick={onOpenAssistant}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-blue-600 hover:bg-blue-500 text-white shadow-sm transition"
              aria-label="Open Contextual AI Assistant"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>AI Assistant</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="border-t border-command-border/60 bg-command-panel/80 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex space-x-1 overflow-x-auto py-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-command-accent/20 text-command-cyan border border-command-accent/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-command-cyan' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Statutory Human-in-the-loop Advisory Banner */}
      <div className="bg-amber-950/40 border-b border-amber-800/30 px-4 py-1 text-center">
        <p className="text-[11px] text-amber-200/90 font-medium">
          <span className="font-semibold text-amber-400">DECISION-SUPPORT NOTICE:</span> AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing.
        </p>
      </div>
    </header>
  );
};
