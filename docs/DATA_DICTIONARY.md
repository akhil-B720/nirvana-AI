# NIRVANA - Comprehensive Data Dictionary

**System:** National Infrastructure Reality & Verification Network using AI (NIRVANA)  
**Version:** 1.0.0  
**Database Standards:** PostgreSQL 15+ / PostGIS with SQLite In-Memory / Local Development Fallback

---

## 1. Core Entities

### 1.1 `projects`
Primary registry of infrastructure works sanctioned under MPLADS.
- `project_id` (VARCHAR(64), Primary Key): Unique sanctioned work identifier.
- `project_name` (VARCHAR(512), NOT NULL): Official title of the sanctioned infrastructure project.
- `project_type` (VARCHAR(64), NOT NULL): Standard category: `BUILDING`, `ROAD`, `BRIDGE`, `WATER_TANK`, `COMMUNITY_HALL`, `DRAINAGE`, `OTHER`.
- `sector` (VARCHAR(128)): Sectoral classification (e.g., `Drinking Water`, `Education`, `Roads & Pathways`, `Health & Sanitation`).
- `state` (VARCHAR(100), NOT NULL): Indian State or Union Territory.
- `district` (VARCHAR(100), NOT NULL): Nodal district.
- `constituency` (VARCHAR(150)): Lok Sabha / Rajya Sabha constituency.
- `block` (VARCHAR(100), NULLABLE): Administrative block or tehsil.
- `village` (VARCHAR(150), NULLABLE): Revenue village or ward.
- `latitude` (DECIMAL(10, 7), NULLABLE): Valid range: -90.0 to 90.0.
- `longitude` (DECIMAL(10, 7), NULLABLE): Valid range: -180.0 to 180.0.
- `sanction_amount` (DECIMAL(15, 2), NOT NULL): Total sanctioned cost in INR (Non-negative).
- `released_amount` (DECIMAL(15, 2), DEFAULT 0.0): Total funds disbursed to implementing agency in INR.
- `expenditure_amount` (DECIMAL(15, 2), DEFAULT 0.0): Total expenditure incurred in INR.
- `start_date` (DATE, NULLABLE): Official commencement date.
- `expected_completion_date` (DATE, NULLABLE): Sanctioned completion deadline.
- `actual_completion_date` (DATE, NULLABLE): Date of physical completion (must be >= start_date).
- `reported_progress` (DECIMAL(5, 2), DEFAULT 0.0): Implementing agency claimed physical progress (0.00 to 100.00).
- `observed_progress` (DECIMAL(5, 2), NULLABLE): Ground-verified/AI-estimated physical progress from evidence (0.00 to 100.00, or `null` if unavailable).
- `observed_progress_status` (VARCHAR(32), DEFAULT 'NOT_AVAILABLE'): Status enum: `NOT_AVAILABLE`, `AI_ESTIMATE`, `OFFICER_VERIFIED`.
- `status` (VARCHAR(32), DEFAULT 'SANCTIONED'): Life-cycle status: `SANCTIONED`, `IN_PROGRESS`, `COMPLETED`, `STALLED`, `CANCELLED`.
- `agency` (VARCHAR(255), NULLABLE): Implementing executive agency / contractor name.
- `source_id` (INTEGER, Foreign Key -> `data_sources.id`): Source record provenance.
- `data_availability_status` (VARCHAR(32), DEFAULT 'PUBLIC_VERIFIED'): `PUBLIC_VERIFIED`, `AUTHORIZED`, `SYNTHETIC`, `INSUFFICIENT_DATA`.
- `data_status` (VARCHAR(30), DEFAULT 'PUBLIC_VERIFIED'): Strict boundary partition: `PUBLIC_VERIFIED` (real MoSPI government data) or `SYNTHETIC` (development test dataset).
- `source_type` (VARCHAR(64), DEFAULT 'OFFICIAL_MPLADS'): `OFFICIAL_MPLADS`, `SYNTHETIC_TEST_DATA`, `OFFICER_UPLOAD`.
- `anomaly_label` (INTEGER, DEFAULT 0): Ground-truth test label for synthetic benchmark: 0 = normal, 1 = potential anomaly.
- `anomaly_category` (VARCHAR(64), NULLABLE): Anomaly typology for benchmark evaluation (e.g. `PAYMENT_PROGRESS_MISMATCH`, `DELAY_PATTERN`, `UNUSUAL_FINANCIAL_PATTERN`).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()): Record creation timestamp.
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()): Last modification timestamp.

---

### 1.2 `data_sources`
Tracks original source provenance, hashes, and compliance.
- `id` (INTEGER, Primary Key, Auto-increment).
- `source_name` (VARCHAR(255), NOT NULL): Descriptive source label.
- `source_url` (VARCHAR(1024), NULLABLE): Web or API origin.
- `source_type` (VARCHAR(64), NOT NULL): `GOVERNMENT_PORTAL`, `OPEN_DATA_CSV`, `OFFICER_UPLOAD`, `SYNTHETIC`.
- `retrieval_timestamp` (TIMESTAMP WITH TIME ZONE, NOT NULL).
- `last_modified` (TIMESTAMP WITH TIME ZONE, NULLABLE).
- `license` (VARCHAR(128), DEFAULT 'NDSAP / Government Open Data').
- `access_method` (VARCHAR(64), DEFAULT 'CSV_INGEST'): Method of receipt.
- `verification_status` (VARCHAR(64), DEFAULT 'PUBLIC_VERIFIED'): Verification status enum.
- `file_hash` (VARCHAR(64), NULLABLE): SHA-256 hash of raw ingested payload.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.3 `project_financials`
Time-series ledger of installments, sanctions, and expenditures.
- `id` (INTEGER, Primary Key, Auto-increment).
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`).
- `transaction_date` (DATE, NOT NULL).
- `transaction_type` (VARCHAR(64), NOT NULL): `SANCTION`, `RELEASE`, `EXPENDITURE`, `REFUND`.
- `amount` (DECIMAL(15, 2), NOT NULL).
- `installment_number` (INTEGER, NULLABLE).
- `utilization_certificate_issued` (BOOLEAN, DEFAULT FALSE).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.4 `project_evidence`
Media and sensor evidence collected for reality grounding.
- `evidence_id` (VARCHAR(64), Primary Key): UUID.
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`).
- `file_name` (VARCHAR(255), NOT NULL).
- `file_hash` (VARCHAR(64), NOT NULL): SHA-256 hash.
- `mime_type` (VARCHAR(100), NOT NULL): Validated MIME (`image/jpeg`, `image/png`, `application/pdf`).
- `file_size` (INTEGER, NOT NULL): Size in bytes.
- `timestamp` (TIMESTAMP WITH TIME ZONE, NOT NULL): Capture time.
- `latitude` (DECIMAL(10, 7), NULLABLE).
- `longitude` (DECIMAL(10, 7), NULLABLE).
- `source` (VARCHAR(128), NOT NULL): `FIELD_INSPECTION`, `CITIZEN_SUBMISSION`, `DRONE_SURVEY`.
- `metadata_json` (JSON / TEXT, NULLABLE): EXIF metadata, camera params, etc.
- `availability_status` (VARCHAR(32), DEFAULT 'AVAILABLE'): `AVAILABLE`, `ARCHIVED`, `CORRUPTED`.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.5 `project_anomalies` & `risk_scores`
Stores fused risk assessments and individual anomaly detector triggers.
- `risk_score_id` (INTEGER, Primary Key, Auto-increment).
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`).
- `fused_risk_score` (DECIMAL(5, 2), NOT NULL): 0.00 to 100.00.
- `risk_tier` (VARCHAR(32), NOT NULL): `NORMAL` (0-30), `WATCH` (31-60), `HIGH` (61-80), `CRITICAL` (81-100).
- `reality_gap_score` (DECIMAL(5, 2), NULLABLE): System analytical score.
- `financial_anomaly_score` (DECIMAL(5, 2), NULLABLE).
- `delay_probability` (DECIMAL(5, 2), NULLABLE).
- `similarity_score` (DECIMAL(5, 2), NULLABLE).
- `document_inconsistency_score` (DECIMAL(5, 2), NULLABLE).
- `contributing_factors_json` (JSON / TEXT): Explanations with actual values.
- `weights_used_json` (JSON / TEXT): Weight configuration applied.
- `model_versions_json` (JSON / TEXT): Exact ML model versions active during inference.
- `confidence_score` (DECIMAL(5, 2), DEFAULT 100.0).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.6 `verification_cases` & `verification_actions`
Human-in-the-loop escalation, field tasks, and officer decisions.
- `case_id` (VARCHAR(64), Primary Key).
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`).
- `assigned_officer_id` (VARCHAR(64), NULLABLE).
- `case_status` (VARCHAR(32), DEFAULT 'OPEN'): `OPEN`, `IN_REVIEW`, `VERIFIED_NORMAL`, `IRREGULARITY_CONFIRMED`, `CLOSED`.
- `priority` (VARCHAR(32), NOT NULL): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `trigger_reason` (TEXT, NOT NULL).
- `recommended_action` (TEXT, NOT NULL).
- `officer_findings` (TEXT, NULLABLE).
- `resolution_timestamp` (TIMESTAMP WITH TIME ZONE, NULLABLE).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.7 `audit_logs`
Immutable tracking for accountability.
- `id` (INTEGER, Primary Key, Auto-increment).
- `user_id` (VARCHAR(64), NOT NULL).
- `action` (VARCHAR(128), NOT NULL): e.g., `EVIDENCE_UPLOAD`, `CASE_RESOLUTION`, `DATA_INGESTION`.
- `project_id` (VARCHAR(64), NULLABLE).
- `previous_value_json` (JSON / TEXT, NULLABLE).
- `new_value_json` (JSON / TEXT, NULLABLE).
- `ip_address` (VARCHAR(45), NULLABLE).
- `timestamp` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.8 `project_component_states`
Granular civil engineering components for physical reality tracking and digital twins.
- `id` (INTEGER, Primary Key, Auto-increment).
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`, NOT NULL).
- `sector` (VARCHAR(64), NOT NULL): Sector categorization (`BUILDING`, `ROAD`, `BRIDGE`, `WATER_TANK`).
- `component_name` (VARCHAR(64), NOT NULL): e.g., `Site Preparation & Earthwork`, `Substructure & RCC Footings`, `Superstructure RCC Framing`.
- `weight_pct` (DECIMAL(5, 2), NOT NULL): Structural milestone weight percentage (sum = 100.0%).
- `completion_pct` (DECIMAL(5, 2), DEFAULT 0.0): Physical completion percentage (0.0 to 100.0).
- `detected_status` (VARCHAR(32), DEFAULT 'NOT_STARTED'): `COMPLETED`, `IN_PROGRESS`, `NOT_STARTED`, `MISSING`.
- `data_status` (VARCHAR(32), DEFAULT 'SYNTHETIC'): Dataset partition tag (`PUBLIC_VERIFIED` or `SYNTHETIC`).
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).

---

### 1.9 `project_progress_history`
Chronological multi-month progress and expenditure snapshots for time-series modeling.
- `id` (INTEGER, Primary Key, Auto-increment).
- `project_id` (VARCHAR(64), Foreign Key -> `projects.project_id`, NOT NULL).
- `record_date` (DATE, NOT NULL): Date of administrative snapshot.
- `reported_progress` (DECIMAL(5, 2), NOT NULL): Claimed completion percentage on snapshot date.
- `financial_expenditure` (DECIMAL(15, 2), DEFAULT 0.0): Cumulative expenditure in INR on snapshot date.
- `status` (VARCHAR(32), DEFAULT 'IN_PROGRESS'): Milestone status enum.
- `data_status` (VARCHAR(32), DEFAULT 'SYNTHETIC'): Dataset partition tag.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW()).
