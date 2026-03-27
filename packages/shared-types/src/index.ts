export type SchoolStatus =
  | "in_school"
  | "out_of_school"
  | "delayed_or_modified"
  | "unclear";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface DistrictSummary {
  name: string;
  canonical_domain: string;
}

export interface SourceSummary {
  id: string;
  title?: string | null;
  url: string;
  source_type: string;
  freshness?: string | null;
  rank_score?: number | null;
}

export interface EvidenceItem {
  type: string;
  label?: string | null;
  matched: boolean;
  source_id?: string | null;
  source_url?: string | null;
  source_title?: string | null;
  snippet?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  parser_interpretation?: string | null;
  freshness?: string | null;
  weight?: number | null;
}

export interface CheckResponse {
  district: DistrictSummary;
  target_date: string;
  status: SchoolStatus;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  explanation: string;
  sources: SourceSummary[];
  evidence: EvidenceItem[];
  result_type: "inferred" | "manual_override";
  last_checked: string;
}

export interface AdminResultSummary {
  id: string;
  district_id: string;
  district_name: string;
  target_date: string;
  status: SchoolStatus;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  explanation: string;
  generated_at: string;
  has_conflict: boolean;
}

