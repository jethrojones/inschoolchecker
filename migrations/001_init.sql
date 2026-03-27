CREATE TABLE IF NOT EXISTS districts (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  canonical_domain VARCHAR(255) UNIQUE NOT NULL,
  homepage_url TEXT NOT NULL,
  cms_type_guess VARCHAR(64),
  timezone VARCHAR(64),
  status VARCHAR(32) DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
  id VARCHAR(36) PRIMARY KEY,
  district_id VARCHAR(36) NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  source_type VARCHAR(64) NOT NULL,
  title VARCHAR(255),
  file_type VARCHAR(64),
  discovered_from_url TEXT,
  rank_score FLOAT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  fetch_status VARCHAR(32) DEFAULT 'pending',
  last_fetched_at TIMESTAMP,
  last_modified_header VARCHAR(255),
  etag VARCHAR(255),
  content_hash VARCHAR(128),
  snapshot_object_key TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parsed_documents (
  id VARCHAR(36) PRIMARY KEY,
  source_id VARCHAR(36) NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  parser_version VARCHAR(32) NOT NULL,
  parse_method VARCHAR(64) NOT NULL,
  school_year_text VARCHAR(128),
  extracted_text TEXT NOT NULL,
  extraction_confidence FLOAT NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_candidates (
  id VARCHAR(36) PRIMARY KEY,
  parsed_document_id VARCHAR(36) NOT NULL REFERENCES parsed_documents(id) ON DELETE CASCADE,
  raw_text TEXT NOT NULL,
  raw_date_text VARCHAR(255),
  start_date DATE,
  end_date DATE,
  label_raw VARCHAR(255),
  label_normalized VARCHAR(255),
  status_effect VARCHAR(64) NOT NULL,
  applies_to VARCHAR(64) NOT NULL DEFAULT 'district_wide',
  confidence FLOAT NOT NULL,
  notes_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inference_results (
  id VARCHAR(36) PRIMARY KEY,
  district_id VARCHAR(36) NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
  target_date DATE NOT NULL,
  status VARCHAR(64) NOT NULL,
  confidence_score FLOAT NOT NULL,
  confidence_level VARCHAR(16) NOT NULL,
  explanation TEXT NOT NULL,
  evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  conflicting_evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  rationale_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  cache_expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inference_results_lookup
  ON inference_results (district_id, target_date, cache_expires_at);

CREATE TABLE IF NOT EXISTS manual_overrides (
  id VARCHAR(36) PRIMARY KEY,
  district_id VARCHAR(36) NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
  target_date DATE NOT NULL,
  status VARCHAR(64) NOT NULL,
  explanation TEXT NOT NULL,
  created_by VARCHAR(255) NOT NULL,
  reason TEXT NOT NULL,
  expires_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fetch_logs (
  id VARCHAR(36) PRIMARY KEY,
  source_id VARCHAR(36) REFERENCES sources(id) ON DELETE SET NULL,
  request_url TEXT NOT NULL,
  response_status INTEGER,
  response_time_ms INTEGER,
  content_type VARCHAR(255),
  robots_checked BOOLEAN NOT NULL DEFAULT FALSE,
  fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
  error_message TEXT
);

