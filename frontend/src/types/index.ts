export interface ProjectListItem {
  project_id: string;
  project_name: string;
  project_type: 'BUILDING' | 'ROAD' | 'BRIDGE' | 'WATER_TANK' | 'COMMUNITY_HALL' | 'DRAINAGE' | 'OTHER';
  sector?: string;
  state: string;
  district: string;
  constituency?: string;
  block?: string;
  village?: string;
  latitude?: number | null;
  longitude?: number | null;
  sanction_amount: number;
  released_amount: number;
  expenditure_amount: number;
  start_date?: string | null;
  expected_completion_date?: string | null;
  actual_completion_date?: string | null;
  reported_progress: number;
  observed_progress?: number | null;
  observed_progress_status: 'NOT_AVAILABLE' | 'AI_ESTIMATE' | 'OFFICER_VERIFIED';
  status: string;
  agency?: string | null;
  data_availability_status: 'PUBLIC_VERIFIED' | 'AUTHORIZED' | 'SYNTHETIC' | 'INSUFFICIENT_DATA';
  fused_risk_score?: number;
  risk_tier?: 'NORMAL' | 'WATCH' | 'HIGH' | 'CRITICAL';
  reality_gap_score?: number | null;
}

export interface FinancialItem {
  id: number;
  transaction_date: string;
  transaction_type: string;
  amount: number;
  installment_number?: number;
}

export interface EventItem {
  id: number;
  event_date: string;
  event_type: string;
  title: string;
  description?: string;
  actor?: string;
}

export interface EvidenceItem {
  evidence_id: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  timestamp: string;
  latitude?: number | null;
  longitude?: number | null;
  source: string;
}

export interface Recommendation {
  action_id: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  trigger: string;
  recommended_action: string;
  action_type: string;
}

export interface RealityGapData {
  project_id: string;
  project_name: string;
  expected_progress?: number | null;
  expected_lower_bound?: number | null;
  expected_upper_bound?: number | null;
  reported_progress: number;
  observed_progress?: number | null;
  observed_progress_status: string;
  financial_utilization: number;
  time_elapsed_ratio?: number | null;
  reality_gap_score: number;
  reality_gap_tier: 'NORMAL' | 'WATCH' | 'HIGH' | 'CRITICAL';
  confidence: number;
  components: {
    financial_progress_gap: number;
    time_progress_gap?: number | null;
    reported_observed_gap?: number | null;
    expected_observed_gap?: number | null;
    document_consistency_gap: number;
  };
  contributing_factors: string[];
  notice: string;
  disclaimer: string;
}

export interface ProjectDetail extends ProjectListItem {
  created_at: string;
  updated_at?: string;
  financials: FinancialItem[];
  events: EventItem[];
  evidence_items: EvidenceItem[];
  risk_summary?: {
    fused_risk_score: number;
    risk_tier: string;
    reality_gap_score?: number;
    financial_anomaly_score?: number;
    delay_probability?: number;
    similarity_score?: number;
    contributing_factors: string[];
  };
  reality_gap_summary?: RealityGapData;
  recommendations: Recommendation[];
}

export interface AnalyticsOverview {
  total_projects: number;
  projects_monitored: number;
  high_risk_projects: number;
  critical_risk_projects: number;
  delayed_projects: number;
  active_reality_gaps: number;
  advisory: string;
}

export interface VerificationCase {
  case_id: string;
  project_id: string;
  project_name: string;
  case_status: 'OPEN' | 'IN_REVIEW' | 'VERIFIED_NORMAL' | 'IRREGULARITY_CONFIRMED' | 'CLOSED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  trigger_reason: string;
  recommended_action: string;
  officer_findings?: string | null;
  created_at: string;
}

export interface ModelRegistryItem {
  model_id: string;
  model_name: string;
  version: string;
  training_data_version: string;
  algorithm: string;
  training_timestamp?: string;
  status: string;
  metrics: Record<string, any>;
}
