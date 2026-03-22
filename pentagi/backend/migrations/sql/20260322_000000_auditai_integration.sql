-- +goose Up
-- +goose StatementBegin

-- Tenants for multi-tenancy support
CREATE TABLE IF NOT EXISTS tenants (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT        NOT NULL,
    slug       TEXT        NOT NULL UNIQUE,
    plan       TEXT        NOT NULL DEFAULT 'free',
    is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ
);

-- Pyramid level test plans
CREATE TYPE PYRAMID_ENGINE AS ENUM (
    'sast',
    'mutation',
    'property_based',
    'fuzzing',
    'integration',
    'contract',
    'differential',
    'e2e',
    'performance',
    'security',
    'chaos',
    'regression',
    'ai_evals',
    'ai_test_gen'
);

CREATE TYPE TEST_MODE AS ENUM (
    'fast',
    'full',
    'regulatory'
);

CREATE TYPE TEST_RUN_STATUS AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE RELEASE_DECISION AS ENUM (
    'green',
    'yellow',
    'red'
);

CREATE TYPE FINDING_SEVERITY AS ENUM (
    'info',
    'low',
    'medium',
    'high',
    'critical'
);

-- Test plans (which engines to run, policies)
CREATE TABLE IF NOT EXISTS test_plans (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       BIGINT       REFERENCES tenants(id) ON DELETE SET NULL,
    flow_id         BIGINT       REFERENCES flows(id) ON DELETE CASCADE,
    name            TEXT         NOT NULL,
    mode            TEST_MODE    NOT NULL DEFAULT 'full',
    engines         TEXT[]       NOT NULL DEFAULT '{}',
    policy          JSONB        NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ
);

-- Test run results per engine
CREATE TABLE IF NOT EXISTS test_runs (
    id                BIGSERIAL PRIMARY KEY,
    test_plan_id      BIGINT           NOT NULL REFERENCES test_plans(id) ON DELETE CASCADE,
    flow_id           BIGINT           REFERENCES flows(id) ON DELETE CASCADE,
    engine            PYRAMID_ENGINE   NOT NULL,
    pyramid_level     INT              NOT NULL DEFAULT 0,
    status            TEST_RUN_STATUS  NOT NULL DEFAULT 'pending',
    score             INT              NOT NULL DEFAULT 0,
    summary           TEXT             NOT NULL DEFAULT '',
    neural_insights   TEXT[]           NOT NULL DEFAULT '{}',
    evidence          JSONB            NOT NULL DEFAULT '{}',
    trace_id          TEXT,
    execution_time_ms BIGINT           NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at        TIMESTAMPTZ
);

-- Findings from test engines
CREATE TABLE IF NOT EXISTS pyramid_findings (
    id              BIGSERIAL PRIMARY KEY,
    test_run_id     BIGINT           NOT NULL REFERENCES test_runs(id) ON DELETE CASCADE,
    flow_id         BIGINT           REFERENCES flows(id) ON DELETE CASCADE,
    engine          PYRAMID_ENGINE   NOT NULL,
    pyramid_level   INT              NOT NULL DEFAULT 0,
    severity        FINDING_SEVERITY NOT NULL DEFAULT 'info',
    category        TEXT             NOT NULL DEFAULT '',
    title           TEXT             NOT NULL,
    description     TEXT             NOT NULL DEFAULT '',
    cwe_id          TEXT,
    file_path       TEXT,
    line_number     INT,
    evidence        JSONB            NOT NULL DEFAULT '{}',
    seed            TEXT,
    neural_score    FLOAT,
    fix_proposal    JSONB,
    is_resolved     BOOLEAN          NOT NULL DEFAULT FALSE,
    is_accepted_risk BOOLEAN         NOT NULL DEFAULT FALSE,
    accepted_by     TEXT,
    acceptance_note TEXT,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ
);

-- Release policies (thresholds for GREEN/YELLOW/RED decisions)
CREATE TABLE IF NOT EXISTS release_policies (
    id                    BIGSERIAL PRIMARY KEY,
    tenant_id             BIGINT      REFERENCES tenants(id) ON DELETE SET NULL,
    flow_id               BIGINT      REFERENCES flows(id) ON DELETE CASCADE,
    name                  TEXT        NOT NULL,
    block_on_critical     BOOLEAN     NOT NULL DEFAULT TRUE,
    block_on_high         BOOLEAN     NOT NULL DEFAULT FALSE,
    min_pyramid_coverage  FLOAT       NOT NULL DEFAULT 0.6,
    min_mutation_score    INT         NOT NULL DEFAULT 60,
    required_engines      TEXT[]      NOT NULL DEFAULT '{}',
    is_default            BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at            TIMESTAMPTZ
);

-- Release gate decisions (GREEN/YELLOW/RED)
CREATE TABLE IF NOT EXISTS release_decisions (
    id                      BIGSERIAL PRIMARY KEY,
    test_plan_id            BIGINT           NOT NULL REFERENCES test_plans(id) ON DELETE CASCADE,
    release_policy_id       BIGINT           REFERENCES release_policies(id) ON DELETE SET NULL,
    flow_id                 BIGINT           REFERENCES flows(id) ON DELETE CASCADE,
    decision                RELEASE_DECISION NOT NULL DEFAULT 'red',
    score                   INT              NOT NULL DEFAULT 0,
    pyramid_coverage        JSONB            NOT NULL DEFAULT '{}',
    blocking_findings       BIGINT[]         NOT NULL DEFAULT '{}',
    summary                 TEXT             NOT NULL DEFAULT '',
    decided_at              TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at              TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMPTZ
);

-- Fix proposals for findings (AI-generated code fixes)
CREATE TABLE IF NOT EXISTS fix_proposals (
    id            BIGSERIAL PRIMARY KEY,
    finding_id    BIGINT      NOT NULL REFERENCES pyramid_findings(id) ON DELETE CASCADE,
    explanation   TEXT        NOT NULL DEFAULT '',
    before_code   TEXT        NOT NULL DEFAULT '',
    after_code    TEXT        NOT NULL DEFAULT '',
    diff          TEXT        NOT NULL DEFAULT '',
    rationale     TEXT        NOT NULL DEFAULT '',
    confidence    FLOAT       NOT NULL DEFAULT 0.0,
    generated_by  TEXT        NOT NULL DEFAULT '',
    pr_url        TEXT,
    pr_number     INT,
    pr_provider   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at    TIMESTAMPTZ
);

-- Immutable audit trail
CREATE TABLE IF NOT EXISTS audit_events (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT      REFERENCES tenants(id) ON DELETE SET NULL,
    user_id       BIGINT      REFERENCES users(id) ON DELETE SET NULL,
    action        TEXT        NOT NULL,
    resource_type TEXT        NOT NULL,
    resource_id   TEXT        NOT NULL DEFAULT '',
    payload       JSONB       NOT NULL DEFAULT '{}',
    ip_address    TEXT        NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Corpus / regression test cases
CREATE TABLE IF NOT EXISTS corpus_cases (
    id            BIGSERIAL PRIMARY KEY,
    flow_id       BIGINT      REFERENCES flows(id) ON DELETE CASCADE,
    engine        TEXT        NOT NULL,
    name          TEXT        NOT NULL,
    input         JSONB       NOT NULL DEFAULT '{}',
    expected      JSONB,
    tags          TEXT[]      NOT NULL DEFAULT '{}',
    is_baseline   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at    TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_runs_test_plan_id     ON test_runs(test_plan_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_flow_id          ON test_runs(flow_id);
CREATE INDEX IF NOT EXISTS idx_pyramid_findings_run_id    ON pyramid_findings(test_run_id);
CREATE INDEX IF NOT EXISTS idx_pyramid_findings_flow_id   ON pyramid_findings(flow_id);
CREATE INDEX IF NOT EXISTS idx_pyramid_findings_severity  ON pyramid_findings(severity);
CREATE INDEX IF NOT EXISTS idx_release_decisions_plan_id  ON release_decisions(test_plan_id);
CREATE INDEX IF NOT EXISTS idx_fix_proposals_finding_id   ON fix_proposals(finding_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_id     ON audit_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id       ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at    ON audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_corpus_cases_flow_id       ON corpus_cases(flow_id);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin

DROP INDEX IF EXISTS idx_corpus_cases_flow_id;
DROP INDEX IF EXISTS idx_audit_events_created_at;
DROP INDEX IF EXISTS idx_audit_events_user_id;
DROP INDEX IF EXISTS idx_audit_events_tenant_id;
DROP INDEX IF EXISTS idx_fix_proposals_finding_id;
DROP INDEX IF EXISTS idx_release_decisions_plan_id;
DROP INDEX IF EXISTS idx_pyramid_findings_severity;
DROP INDEX IF EXISTS idx_pyramid_findings_flow_id;
DROP INDEX IF EXISTS idx_pyramid_findings_run_id;
DROP INDEX IF EXISTS idx_test_runs_flow_id;
DROP INDEX IF EXISTS idx_test_runs_test_plan_id;

DROP TABLE IF EXISTS corpus_cases;
DROP TABLE IF EXISTS audit_events;
DROP TABLE IF EXISTS fix_proposals;
DROP TABLE IF EXISTS release_decisions;
DROP TABLE IF EXISTS release_policies;
DROP TABLE IF EXISTS pyramid_findings;
DROP TABLE IF EXISTS test_runs;
DROP TABLE IF EXISTS test_plans;
DROP TABLE IF EXISTS tenants;

DROP TYPE IF EXISTS FINDING_SEVERITY;
DROP TYPE IF EXISTS RELEASE_DECISION;
DROP TYPE IF EXISTS TEST_RUN_STATUS;
DROP TYPE IF EXISTS TEST_MODE;
DROP TYPE IF EXISTS PYRAMID_ENGINE;

-- +goose StatementEnd
