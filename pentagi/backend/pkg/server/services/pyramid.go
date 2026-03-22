package services

import (
	"net/http"
	"strconv"
	"time"

	"pentagi/pkg/server/logger"
	"pentagi/pkg/server/models"
	"pentagi/pkg/server/response"

	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
)

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
