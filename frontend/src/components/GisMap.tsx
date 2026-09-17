import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { ProjectListItem } from '../types';
import { Layers, MapPin, AlertTriangle, ShieldCheck, Navigation } from 'lucide-react';

interface GisMapProps {
  projects: ProjectListItem[];
  selectedProjectId?: string;
  onSelectProject: (projectId: string) => void;
}

export const GisMap: React.FC<GisMapProps> = ({ projects, selectedProjectId, onSelectProject }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [viewMode, setViewMode] = useState<'RISK' | 'REALITY_GAP' | 'PROGRESS'>('RISK');

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Initialize MapLibre map centered on India
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: [
              'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap, © CartoDB'
          }
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [78.9629, 20.5937], // India center
      zoom: 4.2
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update Markers based on viewMode and project coordinates
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    projects.forEach((p) => {
      if (p.latitude === null || p.longitude === null || p.latitude === undefined || p.longitude === undefined) {
        return;
      }

      // Determine marker color according to mode
      let color = '#3b82f6'; // default blue
      let badge = 'NORMAL';

      if (viewMode === 'RISK') {
        const tier = p.risk_tier || 'NORMAL';
        badge = tier;
        if (tier === 'CRITICAL') color = '#ef4444';
        else if (tier === 'HIGH') color = '#f97316';
        else if (tier === 'WATCH') color = '#f59e0b';
        else color = '#10b981';
      } else if (viewMode === 'REALITY_GAP') {
        const gap = p.reality_gap_score ?? 0;
        if (gap > 40) {
          color = '#ef4444';
          badge = `GAP: ${gap.toFixed(0)}%`;
        } else if (gap > 20) {
          color = '#f59e0b';
          badge = `GAP: ${gap.toFixed(0)}%`;
        } else {
          color = '#10b981';
          badge = 'LOW GAP';
        }
      } else {
        // PROGRESS MODE
        const prog = p.reported_progress;
        badge = `${prog.toFixed(0)}%`;
        if (prog >= 80) color = '#10b981';
        else if (prog >= 40) color = '#0284c7';
        else color = '#eab308';
      }

      const isSelected = p.project_id === selectedProjectId;

      // Custom DOM element for accessible map marker
      const el = document.createElement('div');
      el.className = 'cursor-pointer group flex flex-col items-center';
      el.innerHTML = `
        <div style="background-color: ${color}; border: 2px solid ${isSelected ? '#ffffff' : '#0f172a'}; box-shadow: 0 0 12px ${color}80;" 
             class="w-5 h-5 rounded-full flex items-center justify-center transition-transform transform group-hover:scale-125 ${isSelected ? 'ring-4 ring-cyan-400 scale-125' : ''}">
          <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
        </div>
        <div class="mt-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-slate-900/90 text-slate-200 border border-slate-700 shadow whitespace-nowrap">
          ${badge}
        </div>
      `;

      el.addEventListener('click', () => {
        onSelectProject(p.project_id);
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([p.longitude, p.latitude])
        .addTo(map);

      markersRef.current.push(marker);
    });
  }, [projects, viewMode, selectedProjectId, onSelectProject]);

  // Center on selected project if coordinates exist
  useEffect(() => {
    if (!selectedProjectId || !mapRef.current) return;
    const target = projects.find((p) => p.project_id === selectedProjectId);
    if (target && target.latitude && target.longitude) {
      mapRef.current.flyTo({
        center: [target.longitude, target.latitude],
        zoom: 9.5,
        essential: true,
        speed: 1.2
      });
    }
  }, [selectedProjectId, projects]);

  return (
    <div className="relative w-full h-[520px] rounded-xl border border-command-border overflow-hidden bg-[#070b14] flex flex-col">
      {/* Mode Controls & Legend Header */}
      <div className="absolute top-3 left-3 z-10 bg-command-dark/90 backdrop-blur-md p-2.5 rounded-lg border border-command-border shadow-lg flex flex-col gap-2 max-w-xs">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-command-cyan" />
          <span className="text-xs font-semibold text-white uppercase tracking-wider">GIS Layer Mode</span>
        </div>

        <div className="flex items-center space-x-1">
          {(['RISK', 'REALITY_GAP', 'PROGRESS'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setViewMode(m)}
              className={`px-2 py-1 text-[11px] font-medium rounded transition ${
                viewMode === m
                  ? 'bg-command-accent text-white font-bold shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {m.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Legend */}
        <div className="pt-2 border-t border-slate-800 text-[10px] space-y-1">
          {viewMode === 'RISK' && (
            <div className="flex items-center justify-between text-slate-300">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"/> Normal</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block"/> Watch</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500 inline-block"/> High</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500 inline-block"/> Critical</span>
            </div>
          )}
          {viewMode === 'REALITY_GAP' && (
            <div className="flex items-center justify-between text-slate-300">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"/> &le;20% Gap</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block"/> 20-40%</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500 inline-block"/> &gt;40% Gap</span>
            </div>
          )}
          {viewMode === 'PROGRESS' && (
            <div className="flex items-center justify-between text-slate-300">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block"/> &lt;40%</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-sky-500 inline-block"/> 40-80%</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"/> &ge;80%</span>
            </div>
          )}
        </div>
      </div>

      {/* MapLibre Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />
    </div>
  );
};
