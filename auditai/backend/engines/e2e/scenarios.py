"""
Built-in E2E scenario definitions.
Each scenario describes a user journey with ordered steps and expected assertions.
In production these are supplemented by application-specific scenarios loaded from
the corpus or from a Playwright test suite found in the repo.
"""
from typing import List, Dict, Any


# Generic scenarios that apply to most web applications
GENERIC_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "auth_login_success",
        "type": "authentication",
        "name": "Successful Login Flow",
        "description": "User navigates to login, enters valid credentials, lands on dashboard",
        "steps": [
            {"action": "navigate", "target": "/login"},
            {"action": "fill", "selector": "[name=email]", "value": "{{valid_email}}"},
            {"action": "fill", "selector": "[name=password]", "value": "{{valid_password}}"},
            {"action": "click", "selector": "[type=submit]"},
            {"action": "assert_url", "expected_contains": "/dashboard"},
            {"action": "assert_element", "selector": "[data-testid=user-menu]"},
        ],
        "severity_on_fail": "CRITICAL",
    },
    {
        "id": "auth_login_invalid",
        "type": "authentication",
        "name": "Invalid Credentials Rejected",
        "description": "Login with invalid credentials should show error and not authenticate",
        "steps": [
            {"action": "navigate", "target": "/login"},
            {"action": "fill", "selector": "[name=email]", "value": "invalid@test.com"},
            {"action": "fill", "selector": "[name=password]", "value": "wrongpass"},
            {"action": "click", "selector": "[type=submit]"},
            {"action": "assert_url", "expected_contains": "/login"},
            {"action": "assert_element", "selector": "[data-testid=error-message]"},
            {"action": "assert_not_element", "selector": "[data-testid=user-menu]"},
        ],
        "severity_on_fail": "HIGH",
    },
    {
        "id": "auth_session_expiry",
        "type": "session_management",
        "name": "Session Expiry Redirect",
        "description": "Expired session token should redirect to login without data leak",
        "steps": [
            {"action": "navigate", "target": "/dashboard"},
            {"action": "clear_cookies"},
            {"action": "navigate", "target": "/dashboard"},
            {"action": "assert_url", "expected_contains": "/login"},
        ],
        "severity_on_fail": "HIGH",
    },
    {
        "id": "registration_flow",
        "type": "registration",
        "name": "New User Registration",
        "description": "User can register, receives confirmation, and can log in",
        "steps": [
            {"action": "navigate", "target": "/register"},
            {"action": "fill", "selector": "[name=email]", "value": "{{new_email}}"},
            {"action": "fill", "selector": "[name=password]", "value": "{{strong_password}}"},
            {"action": "fill", "selector": "[name=confirm_password]", "value": "{{strong_password}}"},
            {"action": "click", "selector": "[type=submit]"},
            {"action": "assert_element", "selector": "[data-testid=success-message]"},
        ],
        "severity_on_fail": "HIGH",
    },
    {
        "id": "password_reset",
        "type": "password_reset",
        "name": "Password Reset Flow",
        "description": "Forgot password flow completes successfully",
        "steps": [
            {"action": "navigate", "target": "/forgot-password"},
            {"action": "fill", "selector": "[name=email]", "value": "{{valid_email}}"},
            {"action": "click", "selector": "[type=submit]"},
            {"action": "assert_element", "selector": "[data-testid=reset-email-sent]"},
        ],
        "severity_on_fail": "MEDIUM",
    },
    {
        "id": "data_export_auth",
        "type": "data_export",
        "name": "Data Export Requires Authentication",
        "description": "Export endpoint must reject unauthenticated requests",
        "steps": [
            {"action": "clear_cookies"},
            {"action": "navigate", "target": "/api/export"},
            {"action": "assert_status_code", "expected": 401},
        ],
        "severity_on_fail": "CRITICAL",
    },
    {
        "id": "admin_access_control",
        "type": "admin_access",
        "name": "Admin Panel Access Control",
        "description": "Non-admin user cannot access admin panel",
        "steps": [
            {"action": "login_as", "role": "viewer"},
            {"action": "navigate", "target": "/admin"},
            {"action": "assert_status_code_or_redirect", "expected_not": 200},
        ],
        "severity_on_fail": "CRITICAL",
    },
    {
        "id": "xss_reflected",
        "type": "api_integration",
        "name": "Reflected XSS Prevention",
        "description": "User input in URL parameters is not reflected as executable script",
        "steps": [
            {"action": "navigate", "target": "/search?q=<script>alert(1)</script>"},
            {"action": "assert_no_alert"},
            {"action": "assert_content_not_contains", "text": "<script>alert(1)</script>"},
        ],
        "severity_on_fail": "HIGH",
    },
    {
        "id": "csrf_protection",
        "type": "api_integration",
        "name": "CSRF Token Validation",
        "description": "State-changing requests without CSRF token should be rejected",
        "steps": [
            {"action": "login_as", "role": "user"},
            {"action": "post_without_csrf", "target": "/api/profile", "payload": {"name": "hacked"}},
            {"action": "assert_status_code", "expected": 403},
        ],
        "severity_on_fail": "HIGH",
    },
    {
        "id": "bulk_delete_confirm",
        "type": "bulk_operation",
        "name": "Bulk Delete Requires Confirmation",
        "description": "Bulk destructive actions require explicit user confirmation",
        "steps": [
            {"action": "login_as", "role": "admin"},
            {"action": "navigate", "target": "/admin/users"},
            {"action": "select_all"},
            {"action": "click", "selector": "[data-testid=bulk-delete]"},
            {"action": "assert_element", "selector": "[data-testid=confirm-dialog]"},
            {"action": "assert_no_deletion_yet"},
        ],
        "severity_on_fail": "HIGH",
    },
]

# Banking-specific scenarios
BANKING_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "payment_complete_flow",
        "type": "payment",
        "name": "End-to-End Payment Flow",
        "description": "User initiates, confirms, and receives receipt for a payment",
        "steps": [
            {"action": "login_as", "role": "user"},
            {"action": "navigate", "target": "/payments/new"},
            {"action": "fill", "selector": "[name=amount]", "value": "100.00"},
            {"action": "fill", "selector": "[name=recipient]", "value": "{{valid_account}}"},
            {"action": "click", "selector": "[data-testid=review-payment]"},
            {"action": "assert_element", "selector": "[data-testid=payment-summary]"},
            {"action": "click", "selector": "[data-testid=confirm-payment]"},
            {"action": "assert_element", "selector": "[data-testid=payment-receipt]"},
            {"action": "assert_element_text_contains", "selector": "[data-testid=receipt-amount]", "text": "100.00"},
        ],
        "severity_on_fail": "CRITICAL",
    },
    {
        "id": "transfer_idempotency",
        "type": "transfer",
        "name": "Double-Submit Transfer Prevention",
        "description": "Submitting the same transfer twice should not debit twice",
        "steps": [
            {"action": "login_as", "role": "user"},
            {"action": "navigate", "target": "/transfers/new"},
            {"action": "fill", "selector": "[name=amount]", "value": "50.00"},
            {"action": "double_click_submit", "selector": "[type=submit]"},
            {"action": "assert_single_transaction"},
        ],
        "severity_on_fail": "CRITICAL",
    },
    {
        "id": "balance_display_accuracy",
        "type": "reporting",
        "name": "Balance Displayed Matches Ledger",
        "description": "UI balance must match the server-side ledger balance",
        "steps": [
            {"action": "login_as", "role": "user"},
            {"action": "navigate", "target": "/accounts"},
            {"action": "capture_ui_balance"},
            {"action": "api_get", "target": "/api/accounts/me/balance"},
            {"action": "assert_values_equal", "fields": ["ui_balance", "api_balance"]},
        ],
        "severity_on_fail": "CRITICAL",
    },
]


def get_scenarios_for_stack(stack_info: dict) -> List[Dict[str, Any]]:
    """Select applicable scenarios based on detected stack and domain."""
    scenarios = list(GENERIC_SCENARIOS)
    risk_surfaces = stack_info.get("risk_surfaces", []) if stack_info else []
    domain = stack_info.get("domain", "") if stack_info else ""

    if "banking" in domain.lower() or "financial" in risk_surfaces:
        scenarios.extend(BANKING_SCENARIOS)

    return scenarios
