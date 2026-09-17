import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Layers, Box, RotateCcw, Info, Sliders } from 'lucide-react';

interface ComponentState {
  component_id: string;
  name: string;
  completion_percentage: number;
  status: string;
  color: string;
}

interface DigitalTwinProps {
  projectType: string;
  reportedProgress: number;
  observedProgress?: number | null;
  expectedProgress?: number | null;
  projectName: string;
}

export const DigitalTwin3D: React.FC<DigitalTwinProps> = ({
  projectType,
  reportedProgress,
  observedProgress,
  expectedProgress,
  projectName
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<'REPORTED' | 'OBSERVED' | 'EXPECTED' | 'SIMULATION'>('REPORTED');
  const [simProgress, setSimProgress] = useState<number>(reportedProgress);
  const [activeComponents, setActiveComponents] = useState<ComponentState[]>([]);

  // Determine current active progress
  const currentProgress = 
    mode === 'REPORTED' ? reportedProgress :
    mode === 'OBSERVED' ? (observedProgress ?? 0) :
    mode === 'EXPECTED' ? (expectedProgress ?? 50) :
    simProgress;

  const isObservedMissing = mode === 'OBSERVED' && (observedProgress === null || observedProgress === undefined);

  useEffect(() => {
    if (!mountRef.current || isObservedMissing) return;

    // --- THREE.JS SCENE SETUP ---
    const width = mountRef.current.clientWidth;
    const height = 360;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1120);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(12, 10, 14);
    camera.lookAt(0, 2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    mountRef.current.innerHTML = '';
    mountRef.current.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    dirLight.position.set(15, 20, 15);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const groundGrid = new THREE.GridHelper(20, 20, 0x1e293b, 0x0f172a);
    groundGrid.position.y = 0;
    scene.add(groundGrid);

    // Group for building components
    const modelGroup = new THREE.Group();
    scene.add(modelGroup);

    const p = currentProgress;
    const componentsList: ComponentState[] = [];

    // --- CONSTRUCT 3D GEOMETRIES ACCORDING TO PROJECT TYPE & MILESTONES ---
    if (projectType === 'BUILDING') {
      // 1. Foundation (0-15%)
      if (p > 0) {
        const h = Math.min(1.0, (p / 15.0) * 0.8);
        const geo = new THREE.BoxGeometry(6, h, 6);
        const mat = new THREE.MeshStandardMaterial({ color: 0x78716c, roughness: 0.8 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.y = h / 2;
        modelGroup.add(mesh);
      }
      componentsList.push({ component_id: 'foundation', name: 'Foundation & Plinth', completion_percentage: Math.min(100, (p / 15) * 100), status: p >= 15 ? 'COMPLETED' : p > 0 ? 'IN_PROGRESS' : 'PENDING', color: '#78716c' });

      // 2. Columns (10-35%)
      if (p >= 10) {
        const colH = Math.min(3.5, ((p - 10) / 25.0) * 3.5);
        const colMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
        const positions = [[-2.5, -2.5], [2.5, -2.5], [-2.5, 2.5], [2.5, 2.5], [0, -2.5], [0, 2.5]];
        positions.forEach(([x, z]) => {
          const colGeo = new THREE.BoxGeometry(0.5, colH, 0.5);
          const col = new THREE.Mesh(colGeo, colMat);
          col.position.set(x, 0.8 + colH / 2, z);
          modelGroup.add(col);
        });
      }
      componentsList.push({ component_id: 'columns', name: 'RCC Support Columns', completion_percentage: Math.max(0, Math.min(100, ((p - 10) / 25) * 100)), status: p >= 35 ? 'COMPLETED' : p > 10 ? 'IN_PROGRESS' : 'PENDING', color: '#64748b' });

      // 3. Walls (40-70%)
      if (p >= 40) {
        const wallH = Math.min(3.0, ((p - 40) / 30.0) * 3.0);
        const wallMat = new THREE.MeshStandardMaterial({ color: 0xea580c, roughness: 0.6 });
        const wallGeo = new THREE.BoxGeometry(5.2, wallH, 5.2);
        const wall = new THREE.Mesh(wallGeo, wallMat);
        wall.position.set(0, 0.8 + wallH / 2, 0);
        modelGroup.add(wall);
      }
      componentsList.push({ component_id: 'walls', name: 'Masonry Walls', completion_percentage: Math.max(0, Math.min(100, ((p - 40) / 30) * 100)), status: p >= 70 ? 'COMPLETED' : p > 40 ? 'IN_PROGRESS' : 'PENDING', color: '#ea580c' });

      // 4. Roof Slab (65-80%)
      if (p >= 65) {
        const roofMat = new THREE.MeshStandardMaterial({ color: 0x0284c7 });
        const roofGeo = new THREE.BoxGeometry(6.4, 0.4, 6.4);
        const roof = new THREE.Mesh(roofGeo, roofMat);
        roof.position.set(0, 4.4, 0);
        modelGroup.add(roof);
      }
      componentsList.push({ component_id: 'roof', name: 'RCC Roof Slab', completion_percentage: Math.max(0, Math.min(100, ((p - 65) / 15) * 100)), status: p >= 80 ? 'COMPLETED' : p > 65 ? 'IN_PROGRESS' : 'PENDING', color: '#0284c7' });

      // 5. Finishing (85-100%)
      if (p >= 85) {
        const finMat = new THREE.MeshStandardMaterial({ color: 0x10b981, wireframe: false });
        const beaconGeo = new THREE.CylinderGeometry(0.1, 0.1, 1.2, 8);
        const beacon = new THREE.Mesh(beaconGeo, finMat);
        beacon.position.set(0, 5.2, 0);
        modelGroup.add(beacon);
      }
      componentsList.push({ component_id: 'finishing', name: 'Finishing & Services', completion_percentage: Math.max(0, Math.min(100, ((p - 85) / 15) * 100)), status: p >= 100 ? 'COMPLETED' : p > 85 ? 'IN_PROGRESS' : 'PENDING', color: '#10b981' });

    } else if (projectType === 'ROAD') {
      // Road corridor
      const roadLength = 14;
      const subbaseH = Math.min(0.3, (p / 40.0) * 0.3);
      if (p > 0) {
        const sbGeo = new THREE.BoxGeometry(4.5, subbaseH, roadLength);
        const sbMat = new THREE.MeshStandardMaterial({ color: 0x78716c });
        const sb = new THREE.Mesh(sbGeo, sbMat);
        sb.position.set(0, subbaseH / 2, 0);
        modelGroup.add(sb);
      }
      if (p >= 40) {
        const aspLen = Math.min(roadLength, ((p - 40) / 45.0) * roadLength);
        const aspGeo = new THREE.BoxGeometry(4.0, 0.15, aspLen);
        const aspMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 });
        const asp = new THREE.Mesh(aspGeo, aspMat);
        asp.position.set(0, 0.3 + 0.075, -(roadLength - aspLen) / 2);
        modelGroup.add(asp);
      }
      if (p >= 85) {
        const lineGeo = new THREE.BoxGeometry(0.2, 0.02, roadLength * 0.9);
        const lineMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24 });
        const line = new THREE.Mesh(lineGeo, lineMat);
        line.position.set(0, 0.46, 0);
        modelGroup.add(line);
      }
      componentsList.push({ component_id: 'earthwork', name: 'Sub-Base & Earthwork', completion_percentage: Math.min(100, (p / 40) * 100), status: p >= 40 ? 'COMPLETED' : 'IN_PROGRESS', color: '#78716c' });
      componentsList.push({ component_id: 'asphalt', name: 'Bituminous Macadam', completion_percentage: Math.max(0, Math.min(100, ((p - 40) / 45) * 100)), status: p >= 85 ? 'COMPLETED' : p > 40 ? 'IN_PROGRESS' : 'PENDING', color: '#1e293b' });
      componentsList.push({ component_id: 'markings', name: 'Markings & Signage', completion_percentage: Math.max(0, Math.min(100, ((p - 85) / 15) * 100)), status: p >= 100 ? 'COMPLETED' : p > 85 ? 'IN_PROGRESS' : 'PENDING', color: '#fbbf24' });

    } else {
      // General structure (Bridge / Water tank / Infrastructure fallback)
      const baseH = Math.min(1.0, (p / 25.0) * 1.0);
      if (p > 0) {
        const fGeo = new THREE.CylinderGeometry(3, 3.5, baseH, 16);
        const fMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
        const baseMesh = new THREE.Mesh(fGeo, fMat);
        baseMesh.position.y = baseH / 2;
        modelGroup.add(baseMesh);
      }
      if (p >= 25) {
        const colH = Math.min(4.0, ((p - 25) / 35.0) * 4.0);
        for (let i = 0; i < 4; i++) {
          const angle = (i * Math.PI) / 2;
          const px = Math.cos(angle) * 2;
          const pz = Math.sin(angle) * 2;
          const pGeo = new THREE.CylinderGeometry(0.3, 0.3, colH, 8);
          const pMat = new THREE.MeshStandardMaterial({ color: 0x0284c7 });
          const pillar = new THREE.Mesh(pGeo, pMat);
          pillar.position.set(px, 1.0 + colH / 2, pz);
          modelGroup.add(pillar);
        }
      }
      if (p >= 60) {
        const tankH = Math.min(2.5, ((p - 60) / 30.0) * 2.5);
        const tankGeo = new THREE.CylinderGeometry(2.8, 2.8, tankH, 16);
        const tankMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, opacity: 0.9, transparent: true });
        const tank = new THREE.Mesh(tankGeo, tankMat);
        tank.position.set(0, 5.0 + tankH / 2, 0);
        modelGroup.add(tank);
      }
      componentsList.push({ component_id: 'foundation', name: 'Foundation Staging', completion_percentage: Math.min(100, (p / 25) * 100), status: p >= 25 ? 'COMPLETED' : 'IN_PROGRESS', color: '#64748b' });
      componentsList.push({ component_id: 'superstructure', name: 'Main Superstructure', completion_percentage: Math.max(0, Math.min(100, ((p - 25) / 35) * 100)), status: p >= 60 ? 'COMPLETED' : 'IN_PROGRESS', color: '#0284c7' });
      componentsList.push({ component_id: 'reservoir', name: 'Container & Commissioning', completion_percentage: Math.max(0, Math.min(100, ((p - 60) / 40) * 100)), status: p >= 100 ? 'COMPLETED' : 'IN_PROGRESS', color: '#10b981' });
    }

    setActiveComponents(componentsList);

    // Continuous slow orbit rotation
    let frameId: number;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      modelGroup.rotation.y += 0.005;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      renderer.dispose();
    };
  }, [currentProgress, projectType, isObservedMissing]);

  return (
    <div className="bg-command-panel border border-command-border rounded-xl p-4 flex flex-col">
      {/* Header controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-command-border/70 mb-3">
        <div className="flex items-center space-x-2">
          <Box className="w-5 h-5 text-command-cyan" />
          <span className="text-sm font-semibold text-white">3D Attribute-Driven Digital Twin</span>
          <span className="text-[11px] px-2 py-0.5 font-mono rounded bg-slate-800 text-slate-300 border border-slate-700">
            {projectType}
          </span>
        </div>

        {/* Reality Plane Tabs */}
        <div className="flex items-center space-x-1 bg-command-dark p-1 rounded-lg border border-command-border">
          {(['REPORTED', 'OBSERVED', 'EXPECTED', 'SIMULATION'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-2.5 py-1 text-xs font-medium rounded transition ${
                mode === m
                  ? 'bg-command-accent text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {m === 'SIMULATION' ? 'SIMULATION' : m}
            </button>
          ))}
        </div>
      </div>

      {/* 3D Canvas / Empty State */}
      <div className="relative w-full h-[360px] bg-[#0b1120] rounded-lg border border-command-border/60 overflow-hidden flex items-center justify-center">
        {isObservedMissing ? (
          <div className="text-center p-6 max-w-sm">
            <div className="mx-auto w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center mb-3 border border-slate-700">
              <Info className="w-6 h-6 text-amber-400" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200 mb-1">Physical Evidence Unavailable</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              No ground-verified inspection photo or sensor stream exists for this asset.
              NIRVANA strictly refrains from rendering a fabricated observed 3D twin.
            </p>
          </div>
        ) : (
          <div ref={mountRef} className="w-full h-full" />
        )}

        {/* Current Active Progress Badge */}
        {!isObservedMissing && (
          <div className="absolute top-3 left-3 bg-command-dark/80 backdrop-blur px-3 py-1.5 rounded-md border border-command-border text-xs">
            <span className="text-slate-400">Current Plane: </span>
            <span className="font-bold text-white font-mono">{mode} ({currentProgress.toFixed(1)}%)</span>
          </div>
        )}
      </div>

      {/* Simulation Slider & Milestone Buttons */}
      {mode === 'SIMULATION' && (
        <div className="mt-3 p-3 bg-command-dark/60 rounded-lg border border-command-border/80 flex flex-col space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-300 font-medium flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-command-cyan" />
              Interactive Timeline Simulation Slider:
            </span>
            <span className="font-mono text-command-cyan font-bold">{simProgress.toFixed(0)}%</span>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={simProgress}
            onChange={(e) => setSimProgress(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-command-cyan"
            aria-label="Simulation progress slider"
          />

          <div className="flex items-center justify-between gap-1 pt-1">
            {[0, 20, 40, 60, 80, 100].map((step) => (
              <button
                key={step}
                onClick={() => setSimProgress(step)}
                className={`px-2 py-0.5 text-[11px] font-mono rounded border transition ${
                  simProgress === step
                    ? 'bg-command-cyan/20 border-command-cyan text-command-cyan font-bold'
                    : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                {step}%
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Component Milestone Breakdown */}
      {!isObservedMissing && (
        <div className="mt-3 pt-3 border-t border-command-border/60">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2">
            Structural Milestone Execution Breakdown:
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {activeComponents.map((comp) => (
              <div key={comp.component_id} className="p-2 rounded bg-command-dark/50 border border-command-border/50 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="truncate text-slate-300 font-medium text-[11px]">{comp.name}</span>
                  <span className="font-mono text-[10px] text-command-cyan font-bold">{comp.completion_percentage.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
                  <div
                    className="h-1 rounded-full transition-all duration-300"
                    style={{ width: `${comp.completion_percentage}%`, backgroundColor: comp.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scientific disclaimer notice */}
      <div className="mt-3 text-[11px] text-slate-400/90 italic flex items-center space-x-1.5 pt-2 border-t border-command-border/40">
        <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
        <span>Visualization derived from available project attributes; not a photographic reconstruction.</span>
      </div>
    </div>
  );
};
