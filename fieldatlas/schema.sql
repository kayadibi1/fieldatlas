-- FieldAtlas corpus schema (SQLite)
CREATE TABLE IF NOT EXISTS documents (
    canonical_id   TEXT PRIMARY KEY,
    title          TEXT,
    abstract       TEXT,
    year           INTEGER,
    pub_date       TEXT,
    venue          TEXT,
    doc_type       TEXT,
    sources        TEXT,          -- JSON array of connector names
    source_tiers   TEXT,          -- JSON array of credibility tiers
    n_source_records INTEGER DEFAULT 1,
    relevance      REAL,
    read_tier      INTEGER,        -- 1 | 2 | 3 | NULL
    is_fresh       INTEGER DEFAULT 0,
    oa_pdf_url     TEXT,
    landing_url    TEXT,
    fulltext_status TEXT DEFAULT 'none',  -- none|metadata_only|fetched|parsed
    first_seen_run TEXT,
    last_seen_run  TEXT
);

CREATE TABLE IF NOT EXISTS external_ids (
    canonical_id TEXT,
    scheme       TEXT,            -- doi|arxiv|openalex|s2|dblp|pmid|corpusid|url
    value        TEXT,
    PRIMARY KEY (scheme, value)
);
CREATE INDEX IF NOT EXISTS idx_extid_doc ON external_ids(canonical_id);

CREATE TABLE IF NOT EXISTS authors (
    canonical_id TEXT,
    name         TEXT,
    position     INTEGER
);

CREATE TABLE IF NOT EXISTS citations (
    citing_id TEXT,
    cited_id  TEXT,
    source    TEXT,
    intent    TEXT,
    PRIMARY KEY (citing_id, cited_id)
);

CREATE TABLE IF NOT EXISTS fulltext (
    canonical_id  TEXT PRIMARY KEY,
    format        TEXT,
    parsed_md_path TEXT,
    char_count    INTEGER,
    parse_tool    TEXT,
    parse_status  TEXT,
    content_hash  TEXT
);

CREATE TABLE IF NOT EXISTS extractions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id  TEXT,
    schema_version TEXT,
    fields_json   TEXT,
    coverage_score REAL,
    verify_status TEXT,            -- pending|verified|rejected|not_verified
    reader_model  TEXT,
    run_id        TEXT
);
CREATE INDEX IF NOT EXISTS idx_extr_doc ON extractions(canonical_id);

CREATE TABLE IF NOT EXISTS evidence_spans (
    extraction_id INTEGER,
    canonical_id  TEXT,
    field         TEXT,
    quote         TEXT,
    section       TEXT,
    verified      INTEGER
);

CREATE TABLE IF NOT EXISTS ideas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT,            -- transplant|combination|original
    title         TEXT,
    description   TEXT,
    grounded_doc_ids TEXT,         -- JSON array of canonical_id
    novelty_status TEXT,
    novelty_evidence TEXT,
    feasibility   TEXT,
    assumptions   TEXT,
    dual_use_flag INTEGER DEFAULT 0,
    dual_use_note TEXT,
    score         REAL,
    run_id        TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    started_at  TEXT,
    watermark   TEXT,
    manifest_json TEXT,
    scope_version TEXT
);

CREATE TABLE IF NOT EXISTS harvest_log (
    run_id     TEXT,
    source     TEXT,
    query      TEXT,
    n_returned INTEGER,
    n_new      INTEGER,
    round      INTEGER
);
