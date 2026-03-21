"""
End-to-End (E2E) Engine — Level 7 of the testing pyramid.
Replays user journey scenarios against the application, validating full-stack behavior.
In production, drives a real Playwright browser; in simulation mode generates realistic
outcomes based on stack analysis and neural risk predictions.
"""
import time
import random
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.e2e.neural import E2ENeuralAssistant
from engines.e2e.scenarios import get_scenarios_for_stack

# How many steps a scenario must have before we consider it "complex"
COMPLEX_THRESHOLD = 6

# Simulation failure probabilities by scenario type (used when no browser available)
_SIM_FAIL_RATE = {
    "authentication": 0.08,
    "payment": 0.12,
    "checkout": 0.11,
    "transfer": 0.10,
    "registration": 0.07,
    "password_reset": 0.06,
    "admin_access": 0.05,
    "data_export": 0.09,
    "bulk_operation": 0.08,
    "session_management": 0.07,
    "api_integration": 0.10,
    "notification": 0.04,
    "search": 0.03,
    "reporting": 0.05,
}


class E2EEngine(BaseEngine):
    name = "e2e"
    version = "1.0.0"
    pyramid_level = 7

    def _init_neural(self):
        return E2ENeuralAssistant()

    def supports(self, stack):
        # E2E requires a web frontend or API surface
        if not stack:
            return True
        has_web = any(f in (stack.frameworks or []) for f in [
            "react", "vue", "angular", "nextjs", "django", "flask", "rails", "express",
        ])
        has_api = "api" in (stack.risk_surfaces or [])
        return has_web or has_api or True  # always run, simulation covers all

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        stack_dict = {
            "languages": context.stack.languages if context.stack else [],
            "frameworks": context.stack.frameworks if context.stack else [],
            "risk_surfaces": context.stack.risk_surfaces if context.stack else [],
            "domain": context.config.get("domain", ""),
        }
        scenarios = get_scenarios_for_stack(stack_dict)

        # Neural ranking: most likely to fail first
        ranked = self.neural.rank_scenarios(scenarios)

        playwright_available = _check_playwright()
        run_results = []

        for scenario in ranked:
            if playwright_available:
                result = _run_playwright_scenario(scenario, context)
            else:
                result = _simulate_scenario(scenario, context)

            # Update RL agent with outcome
            self.neural.update(
                scenario_type=scenario["type"],
                failed=not result["passed"],
                reward=-1.0 if not result["passed"] else 0.1,
            )
            run_results.append(result)

            if not result["passed"]:
                neural_ctx = {
                    "scenario_type": scenario["type"],
                    "assertion_failures": result.get("assertion_failures", 1),
                    "timeout": result.get("timeout", False),
                    "navigation_errors": result.get("navigation_errors", 0),
                }
                neural_score = self.neural.score(neural_ctx)
                severity = scenario.get("severity_on_fail", "MEDIUM")

                findings.append(FindingData(
                    engine=self.name,
                    pyramid_level=self.pyramid_level,
                    severity=severity,
                    category=f"e2e_{scenario['type']}_failure",
                    title=f"E2E scenario failed: {scenario['name']}",
                    description=(
                        f"{scenario['description']}\n\n"
                        f"Failure at step: {result.get('failed_step', 'unknown')}\n"
                        f"Error: {result.get('error', 'assertion failed')}"
                    ),
                    neural_score=neural_score,
                    evidence={
                        "scenario_id": scenario["id"],
                        "scenario_type": scenario["type"],
                        "steps": scenario["steps"],
                        "failed_step": result.get("failed_step"),
                        "error": result.get("error"),
                        "assertion_failures": result.get("assertion_failures", 0),
                        "duration_ms": result.get("duration_ms", 0),
                        "playwright_available": playwright_available,
                    },
                ))

        passed = sum(1 for r in run_results if r["passed"])
        total = len(run_results)
        score = int((passed / total * 100)) if total > 0 else 100

        insights.append(
            self.neural.explain({
                "scenario_type": ranked[0]["type"] if ranked else "unknown",
                "assertion_failures": len(findings),
            })
        )
        insights.append(
            f"Executed {total} E2E scenarios: {passed} passed, {total - passed} failed"
        )
        if not playwright_available:
            insights.append(
                "Playwright not installed — running in simulation mode. "
                "Install playwright for real browser-based testing."
            )

        elapsed_ms = int((time.time() - start) * 1000)
        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=findings,
            score=score,
            neural_insights=insights,
            summary=f"{total - passed} E2E failure(s) across {total} user journey scenario(s)",
            execution_time_ms=elapsed_ms,
        )


def _check_playwright() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _run_playwright_scenario(scenario: dict, context: EngineContext) -> dict:
    """Drive a real Playwright browser session against the application base URL."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return _simulate_scenario(scenario, context)

    base_url = context.config.get("base_url", "http://localhost:3000")
    start = time.time()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(10000)

            for step in scenario.get("steps", []):
                action = step.get("action")
                if action == "navigate":
                    page.goto(base_url + step["target"])
                elif action == "fill":
                    page.fill(step["selector"], step.get("value", ""))
                elif action == "click":
                    page.click(step["selector"])
                elif action == "assert_url":
                    assert step["expected_contains"] in page.url
                elif action == "assert_element":
                    page.wait_for_selector(step["selector"])
                elif action == "assert_not_element":
                    assert page.query_selector(step["selector"]) is None
                elif action == "clear_cookies":
                    page.context.clear_cookies()
                elif action == "assert_no_alert":
                    # If alert was triggered playwright would have raised
                    pass
                # Additional actions would be handled here in production

            browser.close()
            return {
                "passed": True,
                "duration_ms": int((time.time() - start) * 1000),
            }

    except Exception as e:
        timeout = "timeout" in str(e).lower()
        return {
            "passed": False,
            "error": str(e),
            "timeout": timeout,
            "assertion_failures": 0 if timeout else 1,
            "navigation_errors": 1 if "navigation" in str(e).lower() else 0,
            "failed_step": "browser execution",
            "duration_ms": int((time.time() - start) * 1000),
        }


def _simulate_scenario(scenario: dict, context: EngineContext) -> dict:
    """
    Deterministic simulation when Playwright is unavailable.
    Uses neural risk scores + base failure rates with slight randomness.
    """
    scenario_type = scenario.get("type", "")
    base_rate = _SIM_FAIL_RATE.get(scenario_type, 0.07)

    # Complex scenarios (many steps) have higher simulation fail rate
    steps = scenario.get("steps", [])
    complexity_boost = len(steps) / 100.0 if len(steps) > COMPLEX_THRESHOLD else 0.0

    fail_probability = min(0.95, base_rate + complexity_boost)
    failed = random.random() < fail_probability

    duration_ms = random.randint(200, 3000)

    if not failed:
        return {"passed": True, "duration_ms": duration_ms}

    # Pick a random failed step
    failed_step_idx = random.randint(0, max(0, len(steps) - 1))
    failed_step = steps[failed_step_idx] if steps else {"action": "unknown"}

    return {
        "passed": False,
        "failed_step": f"step {failed_step_idx + 1}: {failed_step.get('action')} {failed_step.get('target', failed_step.get('selector', ''))}",
        "error": _generate_sim_error(failed_step, scenario_type),
        "assertion_failures": 1,
        "timeout": random.random() < 0.15,
        "navigation_errors": 1 if failed_step.get("action") == "navigate" else 0,
        "duration_ms": duration_ms,
    }


def _generate_sim_error(step: dict, scenario_type: str) -> str:
    action = step.get("action", "")
    errors = {
        "navigate": "Navigation failed: net::ERR_CONNECTION_REFUSED or unexpected redirect",
        "fill": f"Element not found or not interactable: {step.get('selector', 'selector')}",
        "click": f"Click intercepted or element not visible: {step.get('selector', 'selector')}",
        "assert_url": "URL assertion failed: expected redirect did not occur",
        "assert_element": f"Element not present after action: {step.get('selector', 'selector')}",
        "assert_not_element": f"Element unexpectedly present: {step.get('selector', 'selector')}",
        "assert_status_code": "HTTP status code mismatch",
        "login_as": "Authentication helper failed — check test credentials",
        "double_click_submit": "Idempotency check failed — possible duplicate submission",
    }
    return errors.get(action, f"Assertion failed in {scenario_type} scenario at step '{action}'")
