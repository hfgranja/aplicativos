package models

import (
	"fmt"
	"time"

	"github.com/jinzhu/gorm"
)

// PyramidEngine represents a test engine in the universal testing pyramid
type PyramidEngine string

const (
	PyramidEngineSAST          PyramidEngine = "sast"
	PyramidEngineMutation      PyramidEngine = "mutation"
	PyramidEnginePropertyBased PyramidEngine = "property_based"
	PyramidEngineFuzzing       PyramidEngine = "fuzzing"
	PyramidEngineIntegration   PyramidEngine = "integration"
	PyramidEngineContract      PyramidEngine = "contract"
	PyramidEngineDifferential  PyramidEngine = "differential"
	PyramidEngineE2E           PyramidEngine = "e2e"
	PyramidEnginePerformance   PyramidEngine = "performance"
	PyramidEngineSecurity      PyramidEngine = "security"
	PyramidEngineChaos         PyramidEngine = "chaos"
	PyramidEngineRegression    PyramidEngine = "regression"
	PyramidEngineAIEvals       PyramidEngine = "ai_evals"
	PyramidEngineAITestGen     PyramidEngine = "ai_test_gen"
)

// Valid checks if the PyramidEngine value is valid
func (e PyramidEngine) Valid() error {
	switch e {
	case PyramidEngineSAST, PyramidEngineMutation, PyramidEnginePropertyBased,
		PyramidEngineFuzzing, PyramidEngineIntegration, PyramidEngineContract,
		PyramidEngineDifferential, PyramidEngineE2E, PyramidEnginePerformance,
		PyramidEngineSecurity, PyramidEngineChaos, PyramidEngineRegression,
		PyramidEngineAIEvals, PyramidEngineAITestGen:
		return nil
	default:
		return fmt.Errorf("invalid PyramidEngine: %s", e)
	}
}

// Validate implements the gorm validator interface
func (e PyramidEngine) Validate(db *gorm.DB) {
	if err := e.Valid(); err != nil {
		db.AddError(err)
	}
}

// TestMode represents the testing mode (fast, full, regulatory)
type TestMode string

const (
	TestModeFast       TestMode = "fast"
	TestModeFull       TestMode = "full"
	TestModeRegulatory TestMode = "regulatory"
)

// Valid checks if the TestMode value is valid
func (m TestMode) Valid() error {
	switch m {
	case TestModeFast, TestModeFull, TestModeRegulatory:
		return nil
	default:
		return fmt.Errorf("invalid TestMode: %s", m)
	}
}

// TestRunStatus represents the status of a test run
type TestRunStatus string

const (
	TestRunStatusPending   TestRunStatus = "pending"
	TestRunStatusRunning   TestRunStatus = "running"
	TestRunStatusCompleted TestRunStatus = "completed"
	TestRunStatusFailed    TestRunStatus = "failed"
	TestRunStatusCancelled TestRunStatus = "cancelled"
)

// Valid checks if the TestRunStatus value is valid
func (s TestRunStatus) Valid() error {
	switch s {
	case TestRunStatusPending, TestRunStatusRunning, TestRunStatusCompleted,
		TestRunStatusFailed, TestRunStatusCancelled:
		return nil
	default:
		return fmt.Errorf("invalid TestRunStatus: %s", s)
	}
}

// ReleaseDecision represents a release gate decision
type ReleaseDecision string

const (
	ReleaseDecisionGreen  ReleaseDecision = "green"
	ReleaseDecisionYellow ReleaseDecision = "yellow"
	ReleaseDecisionRed    ReleaseDecision = "red"
)

// Valid checks if the ReleaseDecision value is valid
func (d ReleaseDecision) Valid() error {
	switch d {
	case ReleaseDecisionGreen, ReleaseDecisionYellow, ReleaseDecisionRed:
		return nil
	default:
		return fmt.Errorf("invalid ReleaseDecision: %s", d)
	}
}

// FindingSeverity represents the severity of a security finding
type FindingSeverity string

const (
	FindingSeverityInfo     FindingSeverity = "info"
	FindingSeverityLow      FindingSeverity = "low"
	FindingSeverityMedium   FindingSeverity = "medium"
	FindingSeverityHigh     FindingSeverity = "high"
	FindingSeverityCritical FindingSeverity = "critical"
)

// Valid checks if the FindingSeverity value is valid
func (s FindingSeverity) Valid() error {
	switch s {
	case FindingSeverityInfo, FindingSeverityLow, FindingSeverityMedium,
		FindingSeverityHigh, FindingSeverityCritical:
		return nil
	default:
		return fmt.Errorf("invalid FindingSeverity: %s", s)
	}
}

// Tenant is the model for multi-tenancy support
// nolint:lll
type Tenant struct {
	ID        uint64     `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	Name      string     `form:"name" json:"name" validate:"required,max=255" gorm:"type:TEXT;NOT NULL"`
	Slug      string     `form:"slug" json:"slug" validate:"required,max=100" gorm:"type:TEXT;NOT NULL;unique_index"`
	Plan      string     `form:"plan" json:"plan" validate:"required,max=50" gorm:"type:TEXT;NOT NULL;default:'free'"`
	IsActive  bool       `form:"is_active" json:"is_active" gorm:"type:BOOLEAN;NOT NULL;default:true"`
	CreatedAt time.Time  `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt time.Time  `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt *time.Time `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (t *Tenant) TableName() string { return "tenants" }

// Valid validates the Tenant struct
func (t Tenant) Valid() error { return validate.Struct(t) }

// Validate implements the gorm validator interface
func (t Tenant) Validate(db *gorm.DB) {
	if err := t.Valid(); err != nil {
		db.AddError(err)
	}
}

// CreateTenant is the payload for creating a tenant
type CreateTenant struct {
	Name string `form:"name" json:"name" validate:"required,max=255" example:"Acme Corp"`
	Slug string `form:"slug" json:"slug" validate:"required,max=100" example:"acme-corp"`
	Plan string `form:"plan" json:"plan" validate:"omitempty,max=50" example:"enterprise"`
}

// Valid validates the CreateTenant struct
func (c CreateTenant) Valid() error { return validate.Struct(c) }

// TestPlan is the model for a testing plan
// nolint:lll
type TestPlan struct {
	ID        uint64     `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TenantID  *uint64    `form:"tenant_id,omitempty" json:"tenant_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	FlowID    *uint64    `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Name      string     `form:"name" json:"name" validate:"required,max=255" gorm:"type:TEXT;NOT NULL"`
	Mode      TestMode   `form:"mode" json:"mode" validate:"required" gorm:"type:TEST_MODE;NOT NULL;default:'full'"`
	Engines   []string   `form:"engines" json:"engines" gorm:"type:TEXT[];NOT NULL;default:'{}'"`
	Policy    string     `form:"policy" json:"policy" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	CreatedAt time.Time  `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt time.Time  `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt *time.Time `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (tp *TestPlan) TableName() string { return "test_plans" }

// Valid validates the TestPlan struct
func (tp TestPlan) Valid() error { return validate.Struct(tp) }

// Validate implements the gorm validator interface
func (tp TestPlan) Validate(db *gorm.DB) {
	if err := tp.Valid(); err != nil {
		db.AddError(err)
	}
}

// CreateTestPlan is the payload for creating a test plan
// nolint:lll
type CreateTestPlan struct {
	FlowID  *uint64  `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" example:"1"`
	Name    string   `form:"name" json:"name" validate:"required,max=255" example:"Full Security Scan"`
	Mode    TestMode `form:"mode" json:"mode" validate:"required" example:"full"`
	Engines []string `form:"engines" json:"engines" validate:"required" example:"[\"sast\",\"contract\",\"ai_evals\"]"`
}

// Valid validates the CreateTestPlan struct
func (c CreateTestPlan) Valid() error { return validate.Struct(c) }

// TestRun is the model for a single engine test run result
// nolint:lll
type TestRun struct {
	ID              uint64        `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TestPlanID      uint64        `form:"test_plan_id" json:"test_plan_id" validate:"min=1,numeric,required" gorm:"type:BIGINT;NOT NULL"`
	FlowID          *uint64       `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Engine          PyramidEngine `form:"engine" json:"engine" validate:"required" gorm:"type:PYRAMID_ENGINE;NOT NULL"`
	PyramidLevel    int           `form:"pyramid_level" json:"pyramid_level" validate:"min=0" gorm:"type:INT;NOT NULL;default:0"`
	Status          TestRunStatus `form:"status" json:"status" validate:"required" gorm:"type:TEST_RUN_STATUS;NOT NULL;default:'pending'"`
	Score           int           `form:"score" json:"score" validate:"min=0,max=100" gorm:"type:INT;NOT NULL;default:0"`
	Summary         string        `form:"summary" json:"summary" validate:"omitempty" gorm:"type:TEXT;NOT NULL;default:''"`
	NeuralInsights  []string      `form:"neural_insights" json:"neural_insights" gorm:"type:TEXT[];NOT NULL;default:'{}'"`
	Evidence        string        `form:"evidence" json:"evidence" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	TraceID         *string       `form:"trace_id,omitempty" json:"trace_id,omitempty" validate:"omitempty,max=128" gorm:"type:TEXT"`
	ExecutionTimeMs int64         `form:"execution_time_ms" json:"execution_time_ms" validate:"min=0" gorm:"type:BIGINT;NOT NULL;default:0"`
	CreatedAt       time.Time     `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt       time.Time     `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt       *time.Time    `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (tr *TestRun) TableName() string { return "test_runs" }

// Valid validates the TestRun struct
func (tr TestRun) Valid() error { return validate.Struct(tr) }

// Validate implements the gorm validator interface
func (tr TestRun) Validate(db *gorm.DB) {
	if err := tr.Valid(); err != nil {
		db.AddError(err)
	}
}

// PyramidFinding is the model for a security finding from a test engine
// nolint:lll
type PyramidFinding struct {
	ID              uint64          `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TestRunID       uint64          `form:"test_run_id" json:"test_run_id" validate:"min=1,numeric,required" gorm:"type:BIGINT;NOT NULL"`
	FlowID          *uint64         `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Engine          PyramidEngine   `form:"engine" json:"engine" validate:"required" gorm:"type:PYRAMID_ENGINE;NOT NULL"`
	PyramidLevel    int             `form:"pyramid_level" json:"pyramid_level" validate:"min=0" gorm:"type:INT;NOT NULL;default:0"`
	Severity        FindingSeverity `form:"severity" json:"severity" validate:"required" gorm:"type:FINDING_SEVERITY;NOT NULL;default:'info'"`
	Category        string          `form:"category" json:"category" validate:"required,max=255" gorm:"type:TEXT;NOT NULL;default:''"`
	Title           string          `form:"title" json:"title" validate:"required,max=500" gorm:"type:TEXT;NOT NULL"`
	Description     string          `form:"description" json:"description" validate:"omitempty" gorm:"type:TEXT;NOT NULL;default:''"`
	CweID           *string         `form:"cwe_id,omitempty" json:"cwe_id,omitempty" validate:"omitempty,max=50" gorm:"type:TEXT"`
	FilePath        *string         `form:"file_path,omitempty" json:"file_path,omitempty" validate:"omitempty,max=1000" gorm:"type:TEXT"`
	LineNumber      *int            `form:"line_number,omitempty" json:"line_number,omitempty" validate:"omitempty,min=0" gorm:"type:INT"`
	Evidence        string          `form:"evidence" json:"evidence" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	Seed            *string         `form:"seed,omitempty" json:"seed,omitempty" validate:"omitempty" gorm:"type:TEXT"`
	NeuralScore     *float64        `form:"neural_score,omitempty" json:"neural_score,omitempty" validate:"omitempty,min=0,max=1" gorm:"type:FLOAT"`
	FixProposal     *string         `form:"fix_proposal,omitempty" json:"fix_proposal,omitempty" validate:"omitempty" gorm:"type:JSONB"`
	IsResolved      bool            `form:"is_resolved" json:"is_resolved" gorm:"type:BOOLEAN;NOT NULL;default:false"`
	IsAcceptedRisk  bool            `form:"is_accepted_risk" json:"is_accepted_risk" gorm:"type:BOOLEAN;NOT NULL;default:false"`
	AcceptedBy      *string         `form:"accepted_by,omitempty" json:"accepted_by,omitempty" validate:"omitempty,max=255" gorm:"type:TEXT"`
	AcceptanceNote  *string         `form:"acceptance_note,omitempty" json:"acceptance_note,omitempty" validate:"omitempty" gorm:"type:TEXT"`
	ResolvedAt      *time.Time      `form:"resolved_at,omitempty" json:"resolved_at,omitempty" gorm:"type:TIMESTAMPTZ"`
	CreatedAt       time.Time       `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt       time.Time       `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt       *time.Time      `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (f *PyramidFinding) TableName() string { return "pyramid_findings" }

// Valid validates the PyramidFinding struct
func (f PyramidFinding) Valid() error { return validate.Struct(f) }

// Validate implements the gorm validator interface
func (f PyramidFinding) Validate(db *gorm.DB) {
	if err := f.Valid(); err != nil {
		db.AddError(err)
	}
}

// PatchFinding is the payload for updating a finding
type PatchFinding struct {
	Action         string  `form:"action" json:"action" validate:"required,oneof=resolve accept_risk" enums:"resolve,accept_risk" default:"resolve"`
	AcceptanceNote *string `form:"acceptance_note,omitempty" json:"acceptance_note,omitempty" validate:"required_if=Action accept_risk"`
}

// Valid validates the PatchFinding struct
func (p PatchFinding) Valid() error { return validate.Struct(p) }

// ReleasePolicy is the model for release gate policies
// nolint:lll
type ReleasePolicy struct {
	ID                  uint64     `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TenantID            *uint64    `form:"tenant_id,omitempty" json:"tenant_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	FlowID              *uint64    `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Name                string     `form:"name" json:"name" validate:"required,max=255" gorm:"type:TEXT;NOT NULL"`
	BlockOnCritical     bool       `form:"block_on_critical" json:"block_on_critical" gorm:"type:BOOLEAN;NOT NULL;default:true"`
	BlockOnHigh         bool       `form:"block_on_high" json:"block_on_high" gorm:"type:BOOLEAN;NOT NULL;default:false"`
	MinPyramidCoverage  float64    `form:"min_pyramid_coverage" json:"min_pyramid_coverage" validate:"min=0,max=1" gorm:"type:FLOAT;NOT NULL;default:0.6"`
	MinMutationScore    int        `form:"min_mutation_score" json:"min_mutation_score" validate:"min=0,max=100" gorm:"type:INT;NOT NULL;default:60"`
	RequiredEngines     []string   `form:"required_engines" json:"required_engines" gorm:"type:TEXT[];NOT NULL;default:'{}'"`
	IsDefault           bool       `form:"is_default" json:"is_default" gorm:"type:BOOLEAN;NOT NULL;default:false"`
	CreatedAt           time.Time  `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt           time.Time  `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt           *time.Time `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (rp *ReleasePolicy) TableName() string { return "release_policies" }

// Valid validates the ReleasePolicy struct
func (rp ReleasePolicy) Valid() error { return validate.Struct(rp) }

// Validate implements the gorm validator interface
func (rp ReleasePolicy) Validate(db *gorm.DB) {
	if err := rp.Valid(); err != nil {
		db.AddError(err)
	}
}

// CreateReleasePolicy is the payload for creating a release policy
// nolint:lll
type CreateReleasePolicy struct {
	Name               string   `form:"name" json:"name" validate:"required,max=255" example:"Default Policy"`
	BlockOnCritical    bool     `form:"block_on_critical" json:"block_on_critical" example:"true"`
	BlockOnHigh        bool     `form:"block_on_high" json:"block_on_high" example:"false"`
	MinPyramidCoverage float64  `form:"min_pyramid_coverage" json:"min_pyramid_coverage" validate:"min=0,max=1" example:"0.6"`
	MinMutationScore   int      `form:"min_mutation_score" json:"min_mutation_score" validate:"min=0,max=100" example:"60"`
	RequiredEngines    []string `form:"required_engines" json:"required_engines" example:"[\"sast\",\"contract\"]"`
}

// Valid validates the CreateReleasePolicy struct
func (c CreateReleasePolicy) Valid() error { return validate.Struct(c) }

// ReleaseGateDecision is the model for a release gate evaluation result
// nolint:lll
type ReleaseGateDecision struct {
	ID               uint64          `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TestPlanID       uint64          `form:"test_plan_id" json:"test_plan_id" validate:"min=1,numeric,required" gorm:"type:BIGINT;NOT NULL"`
	ReleasePolicyID  *uint64         `form:"release_policy_id,omitempty" json:"release_policy_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	FlowID           *uint64         `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Decision         ReleaseDecision `form:"decision" json:"decision" validate:"required" gorm:"type:RELEASE_DECISION;NOT NULL;default:'red'"`
	Score            int             `form:"score" json:"score" validate:"min=0,max=100" gorm:"type:INT;NOT NULL;default:0"`
	PyramidCoverage  string          `form:"pyramid_coverage" json:"pyramid_coverage" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	BlockingFindings []uint64        `form:"blocking_findings" json:"blocking_findings" gorm:"type:BIGINT[];NOT NULL;default:'{}'"`
	Summary          string          `form:"summary" json:"summary" validate:"omitempty" gorm:"type:TEXT;NOT NULL;default:''"`
	DecidedAt        time.Time       `form:"decided_at,omitempty" json:"decided_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	CreatedAt        time.Time       `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt        time.Time       `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt        *time.Time      `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (rd *ReleaseGateDecision) TableName() string { return "release_decisions" }

// Valid validates the ReleaseGateDecision struct
func (rd ReleaseGateDecision) Valid() error { return validate.Struct(rd) }

// Validate implements the gorm validator interface
func (rd ReleaseGateDecision) Validate(db *gorm.DB) {
	if err := rd.Valid(); err != nil {
		db.AddError(err)
	}
}

// AuditEvent is the model for the immutable audit trail
// nolint:lll
type AuditEvent struct {
	ID           uint64    `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	TenantID     *uint64   `form:"tenant_id,omitempty" json:"tenant_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	UserID       *uint64   `form:"user_id,omitempty" json:"user_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Action       string    `form:"action" json:"action" validate:"required,max=255" gorm:"type:TEXT;NOT NULL"`
	ResourceType string    `form:"resource_type" json:"resource_type" validate:"required,max=100" gorm:"type:TEXT;NOT NULL"`
	ResourceID   string    `form:"resource_id" json:"resource_id" validate:"omitempty,max=255" gorm:"type:TEXT;NOT NULL;default:''"`
	Payload      string    `form:"payload" json:"payload" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	IPAddress    string    `form:"ip_address" json:"ip_address" validate:"omitempty,max=64" gorm:"type:TEXT;NOT NULL;default:''"`
	CreatedAt    time.Time `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
}

// TableName returns the table name
func (ae *AuditEvent) TableName() string { return "audit_events" }

// Valid validates the AuditEvent struct
func (ae AuditEvent) Valid() error { return validate.Struct(ae) }

// CorpusCase is the model for regression test corpus cases
// nolint:lll
type CorpusCase struct {
	ID         uint64     `form:"id" json:"id" validate:"min=0,numeric" gorm:"type:BIGINT;NOT NULL;PRIMARY_KEY;AUTO_INCREMENT"`
	FlowID     *uint64    `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric" gorm:"type:BIGINT"`
	Engine     string     `form:"engine" json:"engine" validate:"required,max=100" gorm:"type:TEXT;NOT NULL"`
	Name       string     `form:"name" json:"name" validate:"required,max=255" gorm:"type:TEXT;NOT NULL"`
	Input      string     `form:"input" json:"input" validate:"omitempty" gorm:"type:JSONB;NOT NULL;default:'{}'"`
	Expected   *string    `form:"expected,omitempty" json:"expected,omitempty" validate:"omitempty" gorm:"type:JSONB"`
	Tags       []string   `form:"tags" json:"tags" gorm:"type:TEXT[];NOT NULL;default:'{}'"`
	IsBaseline bool       `form:"is_baseline" json:"is_baseline" gorm:"type:BOOLEAN;NOT NULL;default:false"`
	CreatedAt  time.Time  `form:"created_at,omitempty" json:"created_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	UpdatedAt  time.Time  `form:"updated_at,omitempty" json:"updated_at,omitempty" gorm:"type:TIMESTAMPTZ;default:CURRENT_TIMESTAMP"`
	DeletedAt  *time.Time `form:"deleted_at,omitempty" json:"deleted_at,omitempty" gorm:"type:TIMESTAMPTZ"`
}

// TableName returns the table name
func (cc *CorpusCase) TableName() string { return "corpus_cases" }

// Valid validates the CorpusCase struct
func (cc CorpusCase) Valid() error { return validate.Struct(cc) }

// Validate implements the gorm validator interface
func (cc CorpusCase) Validate(db *gorm.DB) {
	if err := cc.Valid(); err != nil {
		db.AddError(err)
	}
}

// CreateCorpusCase is the payload for adding a corpus case
type CreateCorpusCase struct {
	FlowID     *uint64  `form:"flow_id,omitempty" json:"flow_id,omitempty" validate:"omitempty,min=1,numeric"`
	Engine     string   `form:"engine" json:"engine" validate:"required,max=100" example:"property_based"`
	Name       string   `form:"name" json:"name" validate:"required,max=255" example:"negative balance test"`
	Input      string   `form:"input" json:"input" validate:"required" example:"{\"amount\": -100}"`
	Expected   *string  `form:"expected,omitempty" json:"expected,omitempty" example:"{\"error\": \"invalid amount\"}"`
	Tags       []string `form:"tags" json:"tags" example:"[\"banking\",\"edge-case\"]"`
	IsBaseline bool     `form:"is_baseline" json:"is_baseline" example:"false"`
}

// Valid validates the CreateCorpusCase struct
func (c CreateCorpusCase) Valid() error { return validate.Struct(c) }

// PyramidSummary is the aggregated view of pyramid coverage
type PyramidSummary struct {
	TestPlanID      uint64                     `json:"test_plan_id"`
	TotalEngines    int                        `json:"total_engines"`
	CompletedRuns   int                        `json:"completed_runs"`
	TotalFindings   int                        `json:"total_findings"`
	CriticalCount   int                        `json:"critical_count"`
	HighCount       int                        `json:"high_count"`
	MediumCount     int                        `json:"medium_count"`
	LowCount        int                        `json:"low_count"`
	OverallScore    int                        `json:"overall_score"`
	PyramidCoverage float64                    `json:"pyramid_coverage"`
	EngineResults   []TestRun                  `json:"engine_results"`
	LatestDecision  *ReleaseGateDecision       `json:"latest_decision,omitempty"`
}
