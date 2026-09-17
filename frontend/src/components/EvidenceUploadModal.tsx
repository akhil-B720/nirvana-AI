import React, { useState } from 'react';
import { api } from '../services/api';
import { ProjectListItem } from '../types';
import { X, Upload, CheckCircle2, AlertCircle, FileText } from 'lucide-react';

interface EvidenceUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  projects: ProjectListItem[];
  onUploadSuccess: () => void;
}

export const EvidenceUploadModal: React.FC<EvidenceUploadModalProps> = ({
  isOpen,
  onClose,
  projects,
  onUploadSuccess
}) => {
  const [projectId, setProjectId] = useState(projects[0]?.project_id || '');
  const [source, setSource] = useState('FIELD_INSPECTION');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [observedProgress, setObservedProgress] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setStatusMsg({ type: 'error', text: 'Please select a file (JPEG, PNG, or PDF)' });
      return;
    }

    setLoading(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('source', source);
    if (latitude) formData.append('latitude', latitude);
    if (longitude) formData.append('longitude', longitude);
    if (observedProgress) formData.append('observed_progress', observedProgress);
    formData.append('file', file);

    try {
      const res = await api.uploadEvidence(formData);
      setStatusMsg({ type: 'success', text: `Uploaded successfully! Hash: ${res.file_hash.slice(0, 12)}...` });
      setTimeout(() => {
        onUploadSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Evidence upload failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-command-panel border border-command-border rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          aria-label="Close modal"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2 text-white font-semibold text-base mb-1">
          <Upload className="w-5 h-5 text-command-cyan" />
          <span>Upload Field Ground Truth Evidence</span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          All evidence is hashed (SHA-256) and anchored directly to the project's permanent audit trail.
        </p>

        {statusMsg && (
          <div className={`p-3 rounded-lg text-xs mb-4 flex items-center space-x-2 ${
            statusMsg.type === 'success' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800' : 'bg-rose-950/80 text-rose-300 border border-rose-800'
          }`}>
            {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>{statusMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-200 focus:outline-none focus:border-command-cyan"
            >
              {projects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  [{p.project_id}] {p.project_name.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Latitude (GPS)</label>
              <input
                type="number"
                step="any"
                placeholder="e.g. 23.2599"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-200 focus:outline-none focus:border-command-cyan"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Longitude (GPS)</label>
              <input
                type="number"
                step="any"
                placeholder="e.g. 77.4126"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-200 focus:outline-none focus:border-command-cyan"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Observed Progress (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                placeholder="e.g. 75.0"
                value={observedProgress}
                onChange={(e) => setObservedProgress(e.target.value)}
                className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-200 focus:outline-none focus:border-command-cyan"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Evidence Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="FIELD_INSPECTION">Field Inspection Photo</option>
                <option value="DRONE_SURVEY">Drone Aerial Survey</option>
                <option value="CITIZEN_SUBMISSION">Citizen Oversight Capture</option>
                <option value="OFFICIAL_MB">Measurement Book (MB)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">File (JPEG, PNG, or PDF)</label>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
              className="w-full bg-command-dark border border-command-border rounded-lg p-2 text-slate-300 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:bg-slate-800 file:text-command-cyan cursor-pointer"
            />
          </div>

          <div className="pt-2 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50 shadow transition"
            >
              {loading ? 'Uploading & Hashing...' : 'Submit Evidence'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
