import {
  ProjectListItem, ProjectDetail, RealityGapData, AnalyticsOverview,
  VerificationCase, ModelRegistryItem
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  // Overview metrics
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  // Project listing with filters
  async getProjects(params: {
    state?: string;
    district?: string;
    project_type?: string;
    risk_tier?: string;
    search?: string;
  } = {}): Promise<ProjectListItem[]> {
    const query = new URLSearchParams();
    if (params.state) query.append('state', params.state);
    if (params.district) query.append('district', params.district);
    if (params.project_type) query.append('project_type', params.project_type);
    if (params.risk_tier) query.append('risk_tier', params.risk_tier);
    if (params.search) query.append('search', params.search);

    const res = await fetch(`${API_BASE}/projects?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  // Single project detail
  async getProjectDetail(id: string): Promise<ProjectDetail> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch project ${id}`);
    return res.json();
  },

  // Reality Gap
  async getRealityGap(id: string): Promise<RealityGapData> {
    const res = await fetch(`${API_BASE}/projects/${id}/reality-gap`);
    if (!res.ok) throw new Error(`Failed to fetch reality gap for ${id}`);
    return res.json();
  },

  // Digital Twin state
  async getDigitalTwin(id: string, simulatedProgress?: number) {
    const query = simulatedProgress !== undefined ? `?simulated_progress=${simulatedProgress}` : '';
    const res = await fetch(`${API_BASE}/projects/${id}/digital-twin${query}`);
    if (!res.ok) throw new Error(`Failed to fetch digital twin for ${id}`);
    return res.json();
  },

  // PDF Report URL
  getReportUrl(id: string): string {
    return `${API_BASE}/projects/${id}/report`;
  },

  // Verification Cases
  async getVerificationCases(): Promise<VerificationCase[]> {
    const res = await fetch(`${API_BASE}/verification-cases`);
    if (!res.ok) throw new Error('Failed to fetch verification cases');
    return res.json();
  },

  async createVerificationCase(data: {
    project_id: string;
    priority: string;
    trigger_reason: string;
    recommended_action: string;
  }) {
    const res = await fetch(`${API_BASE}/verification-cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to create verification case');
    return res.json();
  },

  // Models
  async getModels(): Promise<ModelRegistryItem[]> {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    return res.json();
  },

  // Contextual Assistant
  async askAssistant(query: string, projectId?: string) {
    const res = await fetch(`${API_BASE}/assistant/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, project_id: projectId })
    });
    if (!res.ok) throw new Error('Failed to query assistant');
    return res.json();
  },

  // Evidence upload
  async uploadEvidence(formData: FormData) {
    const res = await fetch(`${API_BASE}/evidence/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  }
};
