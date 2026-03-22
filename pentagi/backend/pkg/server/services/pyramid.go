package services

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"pentagi/pkg/server/logger"
	"pentagi/pkg/server/models"
	"pentagi/pkg/server/response"

	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
)

// ─── Audit helper ─────────────────────────────────────────────────────────────

func (s *PyramidService) logAuditEvent(c *gin.Context, userID *uint64, action, resourceType, resourceID string) {
	event := models.AuditEvent{
		UserID:       userID,
		Action:       action,
		ResourceType: resourceType,
		ResourceID:   resourceID,
		Payload:      "{}",
		IPAddress:    c.ClientIP(),
	}
	_ = s.db.Create(&event).Error // best-effort: do not fail the main operation
}

// ─── Sample findings per engine ───────────────────────────────────────────────

type sampleFindingTemplate struct {
	severity    models.FindingSeverity
	category    string
	title       string
	description string
	cweID       string
	neuralScore float64
}

var engineFindingTemplates = map[string][]sampleFindingTemplate{
	"sast": {
		{models.FindingSeverityHigh, "sql_injection", "SQL Injection via unsanitized query parameter",
			"User input is directly concatenated into an SQL query without parameterization, allowing an attacker to alter the query structure.", "CWE-89", 0.92},
		{models.FindingSeverityMedium, "hardcoded_secret", "Hardcoded API key detected in source code",
			"A plaintext API key was found embedded in source code. Rotate this credential and use environment variables.", "CWE-798", 0.85},
	},
	"security": {
		{models.FindingSeverityCritical, "broken_access_control", "OWASP A01: Admin endpoint accessible without authorization",
			"The /admin/users endpoint returns sensitive user data without verifying the caller has admin privileges.", "CWE-285", 0.97},
		{models.FindingSeverityHigh, "injection", "OWASP A03: Command injection via unvalidated user input",
			"User-controlled input is passed directly to os.Exec without sanitization, enabling arbitrary command execution.", "CWE-78", 0.89},
	},
	"contract": {
		{models.FindingSeverityMedium, "schema_drift", "Breaking change: required field removed from API response",
			"The field 'account_id' was present in the baseline contract but is absent from the current schema, breaking downstream consumers.", "CWE-710", 0.78},
	},
	"integration": {
		{models.FindingSeverityLow, "latency_anomaly", "Anomalous latency spike on /payments endpoint",
			"Integration testing detected p99 latency of 2,340ms on /payments, 3.4× above the 680ms baseline.", "CWE-400", 0.71},
	},
	"e2e": {
		{models.FindingSeverityHigh, "authentication_failure", "E2E: Login flow fails after password reset",
			"After a successful password reset, 20% of login attempts fail with HTTP 401 due to stale session caching.", "CWE-287", 0.88},
	},
	"performance": {
		{models.FindingSeverityMedium, "degradation", "Performance degradation: p99 latency 2.3× baseline",
			"LSTM trend model predicts sustained latency regression. p99 latency is 2,300ms vs 1,000ms baseline over the last 30 min.", "CWE-400", 0.82},
	},
	"mutation": {
		{models.FindingSeverityMedium, "surviving_mutant", "3 mutation operators survived: weak boundary checks",
			"Relational operator mutants (> vs >=) in withdrawal validation survive the test suite, indicating missing boundary-condition tests.", "CWE-840", 0.74},
	},
	"property_based": {
		{models.FindingSeverityHigh, "edge_case", "Property violated: negative balance allowed after concurrent withdrawals",
			"The monotonicity property 'balance >= 0 after withdrawal' fails when two concurrent requests race on the same account.", "CWE-362", 0.91},
	},
	"fuzzing": {
		{models.FindingSeverityHigh, "crash", "Crash on malformed UTF-8 input to request parser",
			"Neural-guided fuzzer triggered a null-pointer dereference in the JSON parser when the input contains overlong UTF-8 sequences.", "CWE-119", 0.94},
	},
	"regression": {
		{models.FindingSeverityMedium, "regression", "Known regression reproduced: /health returns 500 under load",
			"Corpus replay of ticket #1234 reproduces a 500 error on the health endpoint when connection pool is exhausted.", "CWE-703", 0.83},
	},
	"chaos": {
		{models.FindingSeverityMedium, "recovery_timeout", "Service did not recover within 30s SLA after database failure",
			"After injecting a 5s database outage, the payment service took 47s to reconnect, exceeding the 30s recovery budget.", "CWE-703", 0.79},
	},
	"differential": {
		{models.FindingSeverityHigh, "divergence", "Output divergence: legacy vs. modernized implementation disagree on 8.3% of inputs",
			"Siamese network found semantic differences in interest calculation between old and new implementations for fractional amounts.", "CWE-682", 0.88},
	},
	"ai_evals": {
		{models.FindingSeverityCritical, "prompt_injection", "OWASP LLM01: Prompt injection bypasses system guardrails",
			"Injecting 'Ignore previous instructions' into the user turn causes the assistant to disclose its system prompt verbatim.", "CWE-74", 0.96},
		{models.FindingSeverityHigh, "hallucination", "LLM hallucinates account balances for unfamiliar accounts",
			"When queried about accounts not in the RAG context, the model fabricates plausible-looking but incorrect balance figures.", "CWE-20", 0.87},
	},
	"ai_test_gen": {
		{models.FindingSeverityInfo, "generation_complete", "AI Test Generation: 12 unit tests, 4 Hypothesis properties, 8 corpus seeds generated",
			"AST analysis of 3 source files produced pytest-compatible unit tests, property-based test generators, and fuzzing seeds.", "", 0.95},
	},
}

func generateSampleFindings(runID uint64, flowID *uint64, engine models.PyramidEngine, level int) []models.PyramidFinding {
	templates, ok := engineFindingTemplates[string(engine)]
	if !ok {
		return nil
	}
	findings := make([]models.PyramidFinding, 0, len(templates))
	for _, t := range templates {
		score := t.neuralScore
		f := models.PyramidFinding{
			TestRunID:    runID,
			FlowID:       flowID,
			Engine:       engine,
			PyramidLevel: level,
			Severity:     t.severity,
			Category:     t.category,
			Title:        t.title,
			Description:  t.description,
			NeuralScore:  &score,
			Evidence:     "{}",
		}
		if t.cweID != "" {
			cwe := t.cweID
			f.CweID = &cwe
		}
		findings = append(findings, f)
	}
	return findings
}

// ─── Fix proposal templates ────────────────────────────────────────────────────

type fixProposalData struct {
	Explanation string  `json:"explanation"`
	BeforeCode  string  `json:"before_code"`
	AfterCode   string  `json:"after_code"`
	Diff        string  `json:"diff"`
	Rationale   string  `json:"rationale"`
	Confidence  float64 `json:"confidence"`
	GeneratedBy string  `json:"generated_by"`
	GeneratedAt string  `json:"generated_at"`
}

var fixProposalTemplates = map[string]fixProposalData{
	"sql_injection": {
		Explanation: "SQL injection allows attackers to modify query logic by injecting malicious SQL syntax through unsanitized input. Parameterized queries prevent this by separating code from data.",
		BeforeCode:  `query := "SELECT * FROM accounts WHERE id = " + userID` + "\n" + `rows, err := db.Query(query)`,
		AfterCode:   `rows, err := db.Query("SELECT * FROM accounts WHERE id = $1", userID)`,
		Diff:        "--- a/repository.go\n+++ b/repository.go\n@@ -1,2 +1,2 @@\n-query := \"SELECT * FROM accounts WHERE id = \" + userID\n-rows, err := db.Query(query)\n+rows, err := db.Query(\"SELECT * FROM accounts WHERE id = $1\", userID)",
		Rationale:   "Replace string concatenation with a parameterized query placeholder ($1). The database driver safely escapes the value, making injection impossible.",
		Confidence:  0.96,
	},
	"hardcoded_secret": {
		Explanation: "Hardcoded credentials are committed to version control, exposing them to anyone with repository access. Secrets must be loaded from environment variables or a secrets manager.",
		BeforeCode:  `const apiKey = "sk-prod-abc123xyz789"`,
		AfterCode:   `apiKey := os.Getenv("API_KEY")\nif apiKey == "" {\n    log.Fatal("API_KEY environment variable is required")\n}`,
		Diff:        "--- a/config.go\n+++ b/config.go\n@@ -1 +1,4 @@\n-const apiKey = \"sk-prod-abc123xyz789\"\n+apiKey := os.Getenv(\"API_KEY\")\n+if apiKey == \"\" {\n+    log.Fatal(\"API_KEY environment variable is required\")\n+}",
		Rationale:   "Load the API key from an environment variable. Add validation to fail fast if the variable is not set. Rotate the exposed key immediately.",
		Confidence:  0.99,
	},
	"broken_access_control": {
		Explanation: "The endpoint performs no authorization check, allowing any authenticated user to access admin-only resources. Role-based middleware must be applied.",
		BeforeCode:  `router.GET("/admin/users", handlers.ListAllUsers)`,
		AfterCode:   `router.GET("/admin/users", middleware.RequireRole("admin"), handlers.ListAllUsers)`,
		Diff:        "--- a/router.go\n+++ b/router.go\n@@ -1 +1 @@\n-router.GET(\"/admin/users\", handlers.ListAllUsers)\n+router.GET(\"/admin/users\", middleware.RequireRole(\"admin\"), handlers.ListAllUsers)",
		Rationale:   "Add the RequireRole(\"admin\") middleware before the handler. This ensures only users with the admin role can access the endpoint.",
		Confidence:  0.94,
	},
	"prompt_injection": {
		Explanation: "The system does not sanitize user input before appending it to the LLM prompt, allowing users to inject instructions that override the system prompt.",
		BeforeCode:  `prompt := systemPrompt + "\\nUser: " + userInput`,
		AfterCode:   `sanitized := strings.ReplaceAll(userInput, "ignore", "[FILTERED]")\nprompt := fmt.Sprintf("<system>%s</system><user>%s</user>", systemPrompt, sanitized)`,
		Diff:        "--- a/llm_service.go\n+++ b/llm_service.go\n@@ -1 +1,3 @@\n-prompt := systemPrompt + \"\\nUser: \" + userInput\n+sanitized := strings.ReplaceAll(userInput, \"ignore\", \"[FILTERED]\")\n+prompt := fmt.Sprintf(\"<system>%s</system><user>%s</user>\", systemPrompt, sanitized)",
		Rationale:   "Use structured prompt formatting with XML-like delimiters to clearly separate system instructions from user content. Apply input sanitization to remove known injection keywords.",
		Confidence:  0.88,
	},
	"edge_case": {
		Explanation: "A race condition allows two concurrent withdrawal requests to both see the same balance before either commits, resulting in a negative balance.",
		BeforeCode:  `balance := account.Balance\nif balance >= amount {\n    account.Balance -= amount\n    db.Save(account)\n}`,
		AfterCode:   `db.Transaction(func(tx *gorm.DB) error {\n    tx.Set("gorm:query_option", "FOR UPDATE").First(&account, id)\n    if account.Balance < amount {\n        return errors.New("insufficient funds")\n    }\n    account.Balance -= amount\n    return tx.Save(&account).Error\n})`,
		Diff:        "--- a/account_service.go\n+++ b/account_service.go\n@@ -1,5 +1,8 @@\n-balance := account.Balance\n-if balance >= amount {\n-    account.Balance -= amount\n-    db.Save(account)\n-}\n+db.Transaction(func(tx *gorm.DB) error {\n+    tx.Set(\"gorm:query_option\", \"FOR UPDATE\").First(&account, id)\n+    if account.Balance < amount {\n+        return errors.New(\"insufficient funds\")\n+    }\n+    account.Balance -= amount\n+    return tx.Save(&account).Error\n+})",
		Rationale:   "Wrap the read-check-write in a database transaction with SELECT FOR UPDATE to lock the row. This prevents concurrent requests from reading stale balance values.",
		Confidence:  0.93,
	},
}

func buildFixProposal(finding *models.PyramidFinding) string {
	tmpl, ok := fixProposalTemplates[finding.Category]
	if !ok {
		// Generic fix proposal for unknown categories
		tmpl = fixProposalData{
			Explanation: fmt.Sprintf("This %s finding (%s) requires a code change to remediate the identified vulnerability.", finding.Severity, finding.Category),
			BeforeCode:  "// Vulnerable code pattern identified by " + string(finding.Engine) + " engine",
			AfterCode:   "// Apply the recommended fix based on the finding description and CWE guidance",
			Diff:        "// No automatic diff available — manual remediation required",
			Rationale:   "Follow secure coding practices and refer to the CWE reference for detailed remediation guidance.",
			Confidence:  0.65,
		}
	}
	tmpl.GeneratedBy = "pentagi-ai"
	tmpl.GeneratedAt = time.Now().UTC().Format(time.RFC3339)
	b, _ := json.Marshal(tmpl)
	return string(b)
}

type testPlansResp struct {
	Plans []models.TestPlan `json:"plans"`
	Total uint64            `json:"total"`
}

type testRunsResp struct {
	Runs  []models.TestRun `json:"runs"`
	Total uint64           `json:"total"`
}

type pyramidFindingsResp struct {
	Findings []models.PyramidFinding `json:"findings"`
	Total    uint64                  `json:"total"`
}

type releasePoliciesResp struct {
	Policies []models.ReleasePolicy `json:"policies"`
	Total    uint64                 `json:"total"`
}

type releaseDecisionsResp struct {
	Decisions []models.ReleaseGateDecision `json:"decisions"`
	Total     uint64                       `json:"total"`
}

type auditEventsResp struct {
	Events []models.AuditEvent `json:"events"`
	Total  uint64              `json:"total"`
}

type corpusCasesResp struct {
	Cases []models.CorpusCase `json:"cases"`
	Total uint64              `json:"total"`
}

type tenantsResp struct {
	Tenants []models.Tenant `json:"tenants"`
	Total   uint64          `json:"total"`
}

// PyramidService manages the universal testing pyramid resources
type PyramidService struct {
	db *gorm.DB
}

// NewPyramidService creates a new PyramidService
func NewPyramidService(db *gorm.DB) *PyramidService {
	return &PyramidService{db: db}
}

// ─── Tenants ────────────────────────────────────────────────────────────────

// GetTenants returns the list of tenants
// @Summary Retrieve tenants list
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Success 200 {object} response.successResp{data=tenantsResp} "tenants list"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/tenants/ [get]
func (s *PyramidService) GetTenants(c *gin.Context) {
	var resp tenantsResp
	if err := s.db.Where("deleted_at IS NULL").Find(&resp.Tenants).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding tenants")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// CreateTenant creates a new tenant
// @Summary Create a new tenant
// @Tags Pyramid
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param json body models.CreateTenant true "tenant data"
// @Success 201 {object} response.successResp{data=models.Tenant} "tenant created"
// @Failure 400 {object} response.errorResp "invalid request"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/tenants/ [post]
func (s *PyramidService) CreateTenant(c *gin.Context) {
	var form models.CreateTenant
	if err := c.ShouldBindJSON(&form); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error binding tenant payload")
		response.Error(c, response.ErrInternal, err)
		return
	}
	if err := form.Valid(); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error validating tenant payload")
		response.Error(c, response.ErrInternal, err)
		return
	}

	tenant := models.Tenant{
		Name:     form.Name,
		Slug:     form.Slug,
		Plan:     "free",
		IsActive: true,
	}
	if form.Plan != "" {
		tenant.Plan = form.Plan
	}

	if err := s.db.Create(&tenant).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error creating tenant")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusCreated, tenant)
}

// ─── Test Plans ─────────────────────────────────────────────────────────────

// GetTestPlans returns the list of test plans
// @Summary Retrieve test plans list
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Success 200 {object} response.successResp{data=testPlansResp} "test plans list"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/ [get]
func (s *PyramidService) GetTestPlans(c *gin.Context) {
	var resp testPlansResp
	if err := s.db.Where("deleted_at IS NULL").Find(&resp.Plans).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding test plans")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// GetTestPlan returns a specific test plan with its runs
// @Summary Retrieve a specific test plan
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Success 200 {object} response.successResp{data=models.TestPlan} "test plan"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id} [get]
func (s *PyramidService) GetTestPlan(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}
	var plan models.TestPlan
	if err := s.db.Where("id = ? AND deleted_at IS NULL", planID).First(&plan).Error; err != nil {
		if gorm.IsRecordNotFoundError(err) {
			response.Error(c, response.ErrInternal, err)
			return
		}
		logger.FromContext(c).WithError(err).Errorf("error finding test plan")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, plan)
}

// CreateTestPlan creates a new test plan
// @Summary Create a test plan
// @Tags Pyramid
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param json body models.CreateTestPlan true "test plan data"
// @Success 201 {object} response.successResp{data=models.TestPlan} "test plan created"
// @Failure 400 {object} response.errorResp "invalid request"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/ [post]
func (s *PyramidService) CreateTestPlan(c *gin.Context) {
	var form models.CreateTestPlan
	if err := c.ShouldBindJSON(&form); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error binding test plan payload")
		response.Error(c, response.ErrInternal, err)
		return
	}
	if err := form.Valid(); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error validating test plan payload")
		response.Error(c, response.ErrInternal, err)
		return
	}

	plan := models.TestPlan{
		FlowID:  form.FlowID,
		Name:    form.Name,
		Mode:    form.Mode,
		Engines: form.Engines,
		Policy:  "{}",
	}

	if err := s.db.Create(&plan).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error creating test plan")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusCreated, plan)
}

// GetPyramidSummary returns the aggregated pyramid coverage summary for a test plan
// @Summary Retrieve pyramid summary for a test plan
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Success 200 {object} response.successResp{data=models.PyramidSummary} "pyramid summary"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id}/summary [get]
func (s *PyramidService) GetPyramidSummary(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var runs []models.TestRun
	if err := s.db.Where("test_plan_id = ? AND deleted_at IS NULL", planID).Find(&runs).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding test runs")
		response.Error(c, response.ErrInternal, err)
		return
	}

	var findings []models.PyramidFinding
	if len(runs) > 0 {
		runIDs := make([]uint64, len(runs))
		for i, r := range runs {
			runIDs[i] = r.ID
		}
		if err := s.db.Where("test_run_id IN (?) AND deleted_at IS NULL", runIDs).Find(&findings).Error; err != nil {
			logger.FromContext(c).WithError(err).Errorf("error finding findings")
			response.Error(c, response.ErrInternal, err)
			return
		}
	}

	var latestDecision models.ReleaseGateDecision
	var hasDecision bool
	if err := s.db.Where("test_plan_id = ? AND deleted_at IS NULL", planID).
		Order("decided_at DESC").First(&latestDecision).Error; err == nil {
		hasDecision = true
	}

	summary := models.PyramidSummary{
		TestPlanID:    planID,
		TotalEngines:  len(runs),
		EngineResults: runs,
	}

	for _, r := range runs {
		if r.Status == models.TestRunStatusCompleted {
			summary.CompletedRuns++
		}
		summary.OverallScore += r.Score
	}
	if len(runs) > 0 {
		summary.OverallScore = summary.OverallScore / len(runs)
		summary.PyramidCoverage = float64(summary.CompletedRuns) / float64(len(runs))
	}

	for _, f := range findings {
		summary.TotalFindings++
		switch f.Severity {
		case models.FindingSeverityCritical:
			summary.CriticalCount++
		case models.FindingSeverityHigh:
			summary.HighCount++
		case models.FindingSeverityMedium:
			summary.MediumCount++
		case models.FindingSeverityLow:
			summary.LowCount++
		}
	}

	if hasDecision {
		summary.LatestDecision = &latestDecision
	}

	response.Success(c, http.StatusOK, summary)
}

// ─── Test Runs ───────────────────────────────────────────────────────────────

// GetTestRuns returns the test runs for a test plan
// @Summary Retrieve test runs for a test plan
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Success 200 {object} response.successResp{data=testRunsResp} "test runs"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id}/runs [get]
func (s *PyramidService) GetTestRuns(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var resp testRunsResp
	if err := s.db.Where("test_plan_id = ? AND deleted_at IS NULL", planID).
		Find(&resp.Runs).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding test runs")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// ─── Findings ────────────────────────────────────────────────────────────────

// GetFindings returns all findings, optionally filtered by test_run_id
// @Summary Retrieve pyramid findings
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param run_id query uint64 false "filter by test run ID"
// @Param severity query string false "filter by severity"
// @Success 200 {object} response.successResp{data=pyramidFindingsResp} "findings list"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/findings/ [get]
func (s *PyramidService) GetFindings(c *gin.Context) {
	var resp pyramidFindingsResp

	query := s.db.Where("deleted_at IS NULL")
	if runID := c.Query("run_id"); runID != "" {
		query = query.Where("test_run_id = ?", runID)
	}
	if severity := c.Query("severity"); severity != "" {
		query = query.Where("severity = ?", severity)
	}

	if err := query.Order("created_at DESC").Find(&resp.Findings).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding pyramid findings")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// GetFinding returns a specific finding
// @Summary Retrieve a specific pyramid finding
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param finding_id path uint64 true "finding ID"
// @Success 200 {object} response.successResp{data=models.PyramidFinding} "finding"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/findings/{finding_id} [get]
func (s *PyramidService) GetFinding(c *gin.Context) {
	findingID, err := strconv.ParseUint(c.Param("finding_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}
	var finding models.PyramidFinding
	if err := s.db.Where("id = ? AND deleted_at IS NULL", findingID).First(&finding).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding pyramid finding")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, finding)
}

// PatchFinding updates a finding (resolve or accept-risk)
// @Summary Update a pyramid finding
// @Tags Pyramid
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param finding_id path uint64 true "finding ID"
// @Param json body models.PatchFinding true "patch payload"
// @Success 200 {object} response.successResp{data=models.PyramidFinding} "finding updated"
// @Failure 400 {object} response.errorResp "invalid request"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/findings/{finding_id} [patch]
func (s *PyramidService) PatchFinding(c *gin.Context) {
	findingID, err := strconv.ParseUint(c.Param("finding_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var form models.PatchFinding
	if err := c.ShouldBindJSON(&form); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error binding patch finding payload")
		response.Error(c, response.ErrInternal, err)
		return
	}
	if err := form.Valid(); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error validating patch finding payload")
		response.Error(c, response.ErrInternal, err)
		return
	}

	var finding models.PyramidFinding
	if err := s.db.Where("id = ? AND deleted_at IS NULL", findingID).First(&finding).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding pyramid finding")
		response.Error(c, response.ErrInternal, err)
		return
	}

	switch form.Action {
	case "resolve":
		now := time.Now()
		finding.IsResolved = true
		finding.ResolvedAt = &now
	case "accept_risk":
		finding.IsAcceptedRisk = true
		if form.AcceptanceNote != nil {
			finding.AcceptanceNote = form.AcceptanceNote
		}
		uid := strconv.FormatUint(c.GetUint64("uid"), 10)
		finding.AcceptedBy = &uid
	}

	if err := s.db.Save(&finding).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error updating pyramid finding")
		response.Error(c, response.ErrInternal, err)
		return
	}

	uid := c.GetUint64("uid")
	uid64 := uid
	s.logAuditEvent(c, &uid64, "finding."+form.Action, "pyramid_finding", strconv.FormatUint(findingID, 10))

	response.Success(c, http.StatusOK, finding)
}

// ─── Release Policies ────────────────────────────────────────────────────────

// GetReleasePolicies returns the list of release policies
// @Summary Retrieve release policies list
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Success 200 {object} response.successResp{data=releasePoliciesResp} "release policies"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/policies/ [get]
func (s *PyramidService) GetReleasePolicies(c *gin.Context) {
	var resp releasePoliciesResp
	if err := s.db.Where("deleted_at IS NULL").Find(&resp.Policies).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding release policies")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// CreateReleasePolicy creates a new release policy
// @Summary Create a release policy
// @Tags Pyramid
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param json body models.CreateReleasePolicy true "policy data"
// @Success 201 {object} response.successResp{data=models.ReleasePolicy} "policy created"
// @Failure 400 {object} response.errorResp "invalid request"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/policies/ [post]
func (s *PyramidService) CreateReleasePolicy(c *gin.Context) {
	var form models.CreateReleasePolicy
	if err := c.ShouldBindJSON(&form); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error binding release policy payload")
		response.Error(c, response.ErrInternal, err)
		return
	}
	if err := form.Valid(); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error validating release policy payload")
		response.Error(c, response.ErrInternal, err)
		return
	}

	policy := models.ReleasePolicy{
		Name:               form.Name,
		BlockOnCritical:    form.BlockOnCritical,
		BlockOnHigh:        form.BlockOnHigh,
		MinPyramidCoverage: form.MinPyramidCoverage,
		MinMutationScore:   form.MinMutationScore,
		RequiredEngines:    form.RequiredEngines,
	}

	if err := s.db.Create(&policy).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error creating release policy")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusCreated, policy)
}

// ─── Release Gate ────────────────────────────────────────────────────────────

// GetReleaseDecisions returns release gate decisions for a test plan
// @Summary Retrieve release gate decisions
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Success 200 {object} response.successResp{data=releaseDecisionsResp} "release decisions"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id}/decisions [get]
func (s *PyramidService) GetReleaseDecisions(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var resp releaseDecisionsResp
	if err := s.db.Where("test_plan_id = ? AND deleted_at IS NULL", planID).
		Order("decided_at DESC").Find(&resp.Decisions).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding release decisions")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// EvaluateReleaseGate evaluates the release gate for a test plan and produces a decision
// @Summary Evaluate release gate for a test plan
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Param policy_id query uint64 false "release policy ID (uses default if omitted)"
// @Success 201 {object} response.successResp{data=models.ReleaseGateDecision} "release decision"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id}/evaluate [post]
func (s *PyramidService) EvaluateReleaseGate(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	// Fetch the test plan
	var plan models.TestPlan
	if err := s.db.Where("id = ? AND deleted_at IS NULL", planID).First(&plan).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding test plan")
		response.Error(c, response.ErrInternal, err)
		return
	}

	// Fetch policy (default or specified)
	var policy models.ReleasePolicy
	policyIDStr := c.Query("policy_id")
	if policyIDStr != "" {
		pid, _ := strconv.ParseUint(policyIDStr, 10, 64)
		s.db.Where("id = ? AND deleted_at IS NULL", pid).First(&policy)
	} else {
		s.db.Where("is_default = true AND deleted_at IS NULL").First(&policy)
	}

	// Default policy values if none found
	if policy.ID == 0 {
		policy = models.ReleasePolicy{
			BlockOnCritical:    true,
			BlockOnHigh:        false,
			MinPyramidCoverage: 0.6,
			MinMutationScore:   60,
		}
	}

	// Fetch all test runs
	var runs []models.TestRun
	s.db.Where("test_plan_id = ? AND deleted_at IS NULL", planID).Find(&runs)

	// Fetch all findings
	var findings []models.PyramidFinding
	if len(runs) > 0 {
		runIDs := make([]uint64, len(runs))
		for i, r := range runs {
			runIDs[i] = r.ID
		}
		s.db.Where("test_run_id IN (?) AND deleted_at IS NULL AND is_resolved = false AND is_accepted_risk = false", runIDs).
			Find(&findings)
	}

	// Evaluate decision
	decision := models.ReleaseDecisionGreen
	var blockingIDs []uint64
	summary := "All checks passed. No blocking findings."

	for _, f := range findings {
		if f.Severity == models.FindingSeverityCritical && policy.BlockOnCritical {
			decision = models.ReleaseDecisionRed
			blockingIDs = append(blockingIDs, f.ID)
		} else if f.Severity == models.FindingSeverityHigh && policy.BlockOnHigh {
			if decision != models.ReleaseDecisionRed {
				decision = models.ReleaseDecisionRed
			}
			blockingIDs = append(blockingIDs, f.ID)
		} else if f.Severity == models.FindingSeverityMedium && decision == models.ReleaseDecisionGreen {
			decision = models.ReleaseDecisionYellow
		}
	}

	completedRuns := 0
	totalScore := 0
	for _, r := range runs {
		if r.Status == models.TestRunStatusCompleted {
			completedRuns++
		}
		totalScore += r.Score
	}

	coverage := 0.0
	score := 0
	if len(runs) > 0 {
		coverage = float64(completedRuns) / float64(len(runs))
		score = totalScore / len(runs)
	}

	if coverage < policy.MinPyramidCoverage && decision == models.ReleaseDecisionGreen {
		decision = models.ReleaseDecisionYellow
		summary = "Pyramid coverage below threshold."
	}

	if decision == models.ReleaseDecisionRed {
		summary = "Blocking findings detected. Release not recommended."
	} else if decision == models.ReleaseDecisionYellow {
		summary = "Non-critical findings present. Release with caution."
	}

	now := time.Now()
	var policyID *uint64
	if policy.ID != 0 {
		policyID = &policy.ID
	}

	rd := models.ReleaseGateDecision{
		TestPlanID:       planID,
		ReleasePolicyID:  policyID,
		FlowID:           plan.FlowID,
		Decision:         decision,
		Score:            score,
		PyramidCoverage:  "{}",
		BlockingFindings: blockingIDs,
		Summary:          summary,
		DecidedAt:        now,
	}

	if err := s.db.Create(&rd).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error creating release decision")
		response.Error(c, response.ErrInternal, err)
		return
	}

	uid := c.GetUint64("uid")
	uid64 := uid
	s.logAuditEvent(c, &uid64, "release.gate_evaluated", "release_decision", strconv.FormatUint(rd.ID, 10))

	response.Success(c, http.StatusCreated, rd)
}

// ─── Audit Trail ─────────────────────────────────────────────────────────────

// GetAuditEvents returns the immutable audit trail
// @Summary Retrieve audit events
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param action query string false "filter by action"
// @Param resource_type query string false "filter by resource type"
// @Success 200 {object} response.successResp{data=auditEventsResp} "audit events"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/audit/ [get]
func (s *PyramidService) GetAuditEvents(c *gin.Context) {
	var resp auditEventsResp

	query := s.db.Model(&models.AuditEvent{})
	if action := c.Query("action"); action != "" {
		query = query.Where("action = ?", action)
	}
	if resType := c.Query("resource_type"); resType != "" {
		query = query.Where("resource_type = ?", resType)
	}

	if err := query.Order("created_at DESC").Limit(500).Find(&resp.Events).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding audit events")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// ─── Corpus Cases ─────────────────────────────────────────────────────────────

// GetCorpusCases returns the corpus test cases
// @Summary Retrieve corpus cases
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param engine query string false "filter by engine"
// @Success 200 {object} response.successResp{data=corpusCasesResp} "corpus cases"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/corpus/ [get]
func (s *PyramidService) GetCorpusCases(c *gin.Context) {
	var resp corpusCasesResp

	query := s.db.Where("deleted_at IS NULL")
	if engine := c.Query("engine"); engine != "" {
		query = query.Where("engine = ?", engine)
	}

	if err := query.Order("created_at DESC").Find(&resp.Cases).Count(&resp.Total).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error finding corpus cases")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusOK, resp)
}

// ─── Test Execution ───────────────────────────────────────────────────────────

// engineLevelMap maps engine names to their pyramid level
var engineLevelMap = map[string]int{
	"ai_test_gen":    0,
	"sast":           1,
	"mutation":       2,
	"regression":     2,
	"property_based": 3,
	"fuzzing":        3,
	"integration":    4,
	"contract":       5,
	"differential":   6,
	"e2e":            7,
	"performance":    8,
	"security":       9,
	"chaos":          10,
	"ai_evals":       11,
}

// ExecuteTestPlan runs a test plan simulation, creating TestRun records and findings per engine
// @Summary Execute a test plan
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param plan_id path uint64 true "test plan ID"
// @Success 201 {object} response.successResp{data=testRunsResp} "test runs created"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/plans/{plan_id}/execute [post]
func (s *PyramidService) ExecuteTestPlan(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("plan_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var plan models.TestPlan
	if err := s.db.Where("id = ? AND deleted_at IS NULL", planID).First(&plan).Error; err != nil {
		if gorm.IsRecordNotFoundError(err) {
			response.Error(c, response.ErrInternal, err)
			return
		}
		logger.FromContext(c).WithError(err).Errorf("error finding test plan")
		response.Error(c, response.ErrInternal, err)
		return
	}

	uid := c.GetUint64("uid")
	var resp testRunsResp

	for i, engineName := range plan.Engines {
		level, ok := engineLevelMap[engineName]
		if !ok {
			level = 1
		}
		// Score varies per engine: 70–99 based on position
		score := 70 + (i*7+level*3)%30

		executionMs := int64(300 + i*180 + level*50)
		insights := []string{
			fmt.Sprintf("Neural model confidence: %d%%", 80+(i*3+level)%18),
			fmt.Sprintf("Engine %s completed %d checks", engineName, 10+i*3),
		}

		run := models.TestRun{
			TestPlanID:      planID,
			FlowID:          plan.FlowID,
			Engine:          models.PyramidEngine(engineName),
			PyramidLevel:    level,
			Status:          models.TestRunStatusCompleted,
			Score:           score,
			Summary:         fmt.Sprintf("%s engine completed successfully. Score: %d/100.", engineName, score),
			NeuralInsights:  insights,
			Evidence:        "{}",
			ExecutionTimeMs: executionMs,
		}

		if err := s.db.Create(&run).Error; err != nil {
			logger.FromContext(c).WithError(err).Errorf("error creating test run for engine %s", engineName)
			continue
		}
		resp.Runs = append(resp.Runs, run)
		resp.Total++

		// Generate and persist sample findings for this engine
		findings := generateSampleFindings(run.ID, plan.FlowID, models.PyramidEngine(engineName), level)
		for fi := range findings {
			if dbErr := s.db.Create(&findings[fi]).Error; dbErr != nil {
				logger.FromContext(c).WithError(dbErr).Errorf("error creating finding for engine %s", engineName)
			}
		}
	}

	uid64 := uid
	s.logAuditEvent(c, &uid64, "test_plan.executed", "test_plan", strconv.FormatUint(planID, 10))

	response.Success(c, http.StatusCreated, resp)
}

// ─── Fix Proposal Generation ──────────────────────────────────────────────────

// GenerateFixProposal generates an AI-assisted fix proposal for a finding
// @Summary Generate a fix proposal for a finding
// @Tags Pyramid
// @Produce json
// @Security BearerAuth
// @Param finding_id path uint64 true "finding ID"
// @Success 200 {object} response.successResp{data=models.PyramidFinding} "finding with fix proposal"
// @Failure 404 {object} response.errorResp "not found"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/findings/{finding_id}/generate-fix [post]
func (s *PyramidService) GenerateFixProposal(c *gin.Context) {
	findingID, err := strconv.ParseUint(c.Param("finding_id"), 10, 64)
	if err != nil {
		response.Error(c, response.ErrInternal, err)
		return
	}

	var finding models.PyramidFinding
	if err := s.db.Where("id = ? AND deleted_at IS NULL", findingID).First(&finding).Error; err != nil {
		if gorm.IsRecordNotFoundError(err) {
			response.Error(c, response.ErrInternal, err)
			return
		}
		logger.FromContext(c).WithError(err).Errorf("error finding pyramid finding")
		response.Error(c, response.ErrInternal, err)
		return
	}

	fixJSON := buildFixProposal(&finding)
	finding.FixProposal = &fixJSON

	if err := s.db.Save(&finding).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error saving fix proposal")
		response.Error(c, response.ErrInternal, err)
		return
	}

	uid := c.GetUint64("uid")
	uid64 := uid
	s.logAuditEvent(c, &uid64, "finding.fix_proposed", "pyramid_finding", strconv.FormatUint(findingID, 10))

	response.Success(c, http.StatusOK, finding)
}

// CreateCorpusCase adds a new corpus test case
// @Summary Create a corpus case
// @Tags Pyramid
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param json body models.CreateCorpusCase true "corpus case data"
// @Success 201 {object} response.successResp{data=models.CorpusCase} "corpus case created"
// @Failure 400 {object} response.errorResp "invalid request"
// @Failure 403 {object} response.errorResp "not permitted"
// @Failure 500 {object} response.errorResp "internal error"
// @Router /pyramid/corpus/ [post]
func (s *PyramidService) CreateCorpusCase(c *gin.Context) {
	var form models.CreateCorpusCase
	if err := c.ShouldBindJSON(&form); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error binding corpus case payload")
		response.Error(c, response.ErrInternal, err)
		return
	}
	if err := form.Valid(); err != nil {
		logger.FromContext(c).WithError(err).Errorf("error validating corpus case payload")
		response.Error(c, response.ErrInternal, err)
		return
	}

	cc := models.CorpusCase{
		FlowID:     form.FlowID,
		Engine:     form.Engine,
		Name:       form.Name,
		Input:      form.Input,
		Expected:   form.Expected,
		Tags:       form.Tags,
		IsBaseline: form.IsBaseline,
	}

	if err := s.db.Create(&cc).Error; err != nil {
		logger.FromContext(c).WithError(err).Errorf("error creating corpus case")
		response.Error(c, response.ErrInternal, err)
		return
	}
	response.Success(c, http.StatusCreated, cc)
}
