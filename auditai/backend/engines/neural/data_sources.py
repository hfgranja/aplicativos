"""
Data Source Connectors
======================
Real-time connectors to vulnerability databases, academic paper repositories,
and AI-generated bug datasets. All sources feed the neural knowledge base.

Sources:
  NVDConnector          → NIST NVD CVE API v2.0  (https://nvd.nist.gov/)
  ArxivConnector        → arXiv cs.CR + cs.SE papers (https://arxiv.org/search/)
  BigVulLoader          → 188k C/C++ vulnerable functions (HuggingFace)
  CWECatalogLoader      → MITRE CWE Top 25 + full catalog
  GitHubAdvisoryLoader  → GitHub Security Advisories API
  SWEBenchLoader        → SWE-bench Python bug benchmark (princeton-nlp/SWE-bench)
  OWASPKnowledgeBase    → OWASP Top 10 + LLM Top 10 (inline, always available)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# ── Lazy import helpers ────────────────────────────────────────────────────────

def _httpx():
    try:
        import httpx
        return httpx
    except ImportError:
        raise ImportError("httpx is required for data source connectors. Run: pip install httpx")


def _datasets():
    try:
        import datasets
        return datasets
    except ImportError:
        raise ImportError("datasets is required for BigVul/SWE-bench. Run: pip install datasets")


# ── Data transfer objects ──────────────────────────────────────────────────────

@dataclass
class CVERecord:
    cve_id: str
    description: str
    published: str
    severity: str          # CRITICAL / HIGH / MEDIUM / LOW / NONE
    cvss_score: float
    cwe_ids: list[str]
    references: list[str]
    affected_products: list[str] = field(default_factory=list)


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    published: str
    categories: list[str]
    url: str
    fix_techniques: list[str] = field(default_factory=list)   # extracted by heuristic


@dataclass
class VulnCodeSample:
    sample_id: str
    source: str            # bigvul | swebench | d2a | github
    language: str
    vulnerable_code: str
    fixed_code: str | None
    vulnerability_type: str
    cwe_id: str | None
    description: str
    severity: str
    commit_url: str | None = None


@dataclass
class CWEEntry:
    cwe_id: str
    name: str
    description: str
    extended_description: str
    category: str
    likelihood: str
    consequences: list[str]
    mitigations: list[str]
    detection_methods: list[str]
    related_cwes: list[str]


# ── NVD CVE Connector ─────────────────────────────────────────────────────────

class NVDConnector:
    """
    Connects to the NIST National Vulnerability Database API v2.0.
    Fetches CVE records with descriptions, CVSS scores, and CWE mappings.
    Rate limit: 5 req/30s without API key; 50 req/30s with API key.
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._headers = {"apiKey": api_key} if api_key else {}

    async def search(
        self,
        keyword: str | None = None,
        cwe_id: str | None = None,
        severity: str | None = None,
        start_index: int = 0,
        results_per_page: int = 50,
    ) -> list[CVERecord]:
        params: dict[str, Any] = {
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, 2000),
        }
        if keyword:
            params["keywordSearch"] = keyword
        if cwe_id:
            params["cweId"] = cwe_id
        if severity:
            params["cvssV3Severity"] = severity.upper()

        url = f"{self.BASE_URL}?{urlencode(params)}"
        httpx = _httpx()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("NVD API error: %s", exc)
            return []

        records = []
        for vuln in data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            try:
                records.append(self._parse_cve(cve))
            except Exception:
                continue
        return records

    async def fetch_recent(self, days: int = 7, max_results: int = 200) -> list[CVERecord]:
        """Fetch CVEs published in the last `days` days."""
        from datetime import datetime, timedelta, timezone
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        params = {
            "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": end.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": min(max_results, 2000),
            "startIndex": 0,
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        httpx = _httpx()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("NVD recent CVE fetch error: %s", exc)
            return []

        return [self._parse_cve(v["cve"]) for v in data.get("vulnerabilities", []) if "cve" in v]

    def _parse_cve(self, cve: dict) -> CVERecord:
        cve_id = cve.get("id", "")

        # Description (prefer English)
        desc = ""
        for d in cve.get("descriptions", []):
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break

        # CVSS score + severity
        cvss_score = 0.0
        severity = "NONE"
        metrics = cve.get("metrics", {})
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            mlist = metrics.get(key, [])
            if mlist:
                m = mlist[0].get("cvssData", {})
                cvss_score = float(m.get("baseScore", 0.0))
                severity = m.get("baseSeverity", mlist[0].get("baseSeverity", "NONE"))
                break

        # CWE IDs
        cwe_ids = [
            w.get("value", "")
            for w in cve.get("weaknesses", [])
            for w in w.get("description", [])
            if w.get("lang") == "en" and w.get("value", "").startswith("CWE-")
        ]

        # References
        refs = [r.get("url", "") for r in cve.get("references", [])]

        published = cve.get("published", "")

        return CVERecord(
            cve_id=cve_id,
            description=desc,
            published=published,
            severity=severity,
            cvss_score=cvss_score,
            cwe_ids=list(set(cwe_ids)),
            references=refs[:10],
        )


# ── arXiv Connector ───────────────────────────────────────────────────────────

class ArxivConnector:
    """
    Searches arXiv for security and software engineering papers.
    Uses the arXiv API v2 (Atom/XML feed).
    Key categories: cs.CR (Security), cs.SE (Software Engineering), cs.LG (ML)
    """

    BASE_URL = "https://export.arxiv.org/api/query"

    # Heuristic keywords that indicate a paper contains fix/repair techniques
    FIX_KEYWORDS = [
        "automated repair", "bug fix", "patch generation", "program repair",
        "vulnerability patch", "code repair", "fix synthesis", "defect repair",
        "automated program fixing", "neural program repair",
    ]

    async def search(
        self,
        query: str,
        categories: list[str] | None = None,
        max_results: int = 50,
        sort_by: str = "relevance",
    ) -> list[ArxivPaper]:
        cats = categories or ["cs.CR", "cs.SE"]
        cat_filter = " OR ".join(f"cat:{c}" for c in cats)
        full_query = f"({query}) AND ({cat_filter})"

        params = {
            "search_query": full_query,
            "max_results": min(max_results, 200),
            "sortBy": sort_by,
            "sortOrder": "descending",
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        httpx = _httpx()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.text
        except Exception as exc:
            logger.warning("arXiv API error: %s", exc)
            return []

        return self._parse_feed(content)

    async def fetch_vulnerability_detection_papers(self, max_results: int = 100) -> list[ArxivPaper]:
        return await self.search(
            query="vulnerability detection deep learning code",
            categories=["cs.CR", "cs.SE", "cs.LG"],
            max_results=max_results,
        )

    async def fetch_automated_repair_papers(self, max_results: int = 100) -> list[ArxivPaper]:
        return await self.search(
            query="automated program repair bug fix neural network",
            categories=["cs.SE", "cs.PL", "cs.LG"],
            max_results=max_results,
        )

    async def fetch_llm_security_papers(self, max_results: int = 100) -> list[ArxivPaper]:
        return await self.search(
            query="large language model security vulnerability code generation",
            categories=["cs.CR", "cs.SE", "cs.LG"],
            max_results=max_results,
        )

    def _parse_feed(self, xml_content: str) -> list[ArxivPaper]:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            logger.warning("arXiv XML parse error: %s", exc)
            return []

        for entry in root.findall("atom:entry", ns):
            try:
                arxiv_id = entry.findtext("atom:id", "", ns).split("/abs/")[-1]
                title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
                abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
                published = entry.findtext("atom:published", "", ns)
                authors = [
                    a.findtext("atom:name", "", ns)
                    for a in entry.findall("atom:author", ns)
                ]
                categories = [
                    c.get("term", "")
                    for c in entry.findall("atom:category", ns)
                ]
                url = f"https://arxiv.org/abs/{arxiv_id}"
                fix_techniques = self._extract_techniques(abstract)
                papers.append(ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    published=published,
                    categories=categories,
                    url=url,
                    fix_techniques=fix_techniques,
                ))
            except Exception:
                continue
        return papers

    def _extract_techniques(self, abstract: str) -> list[str]:
        lower = abstract.lower()
        return [kw for kw in self.FIX_KEYWORDS if kw in lower]


# ── BigVul Loader ─────────────────────────────────────────────────────────────

class BigVulLoader:
    """
    Loads the BigVul dataset: 188,636 C/C++ code changes from 348 GitHub projects,
    labelled as vulnerable or non-vulnerable at function level.
    Source: HuggingFace datasets — VulnHub/bigvul (or local CSV fallback)
    Paper: "A C/C++ Code Vulnerability Dataset with Code Changes and CVE Summaries" (Fan et al. 2020)
    """

    HF_DATASET = "VulnHub/bigvul"
    FALLBACK_URL = (
        "https://raw.githubusercontent.com/VulnHub/vul4j/main/data/bigvul_sample.csv"
    )

    def load(self, split: str = "train", max_samples: int = 10_000) -> list[VulnCodeSample]:
        """Load samples from HuggingFace datasets. Falls back to empty list if unavailable."""
        try:
            ds_lib = _datasets()
            dataset = ds_lib.load_dataset(self.HF_DATASET, split=split, trust_remote_code=True)
            samples = []
            for i, row in enumerate(dataset):
                if i >= max_samples:
                    break
                samples.append(self._row_to_sample(row))
            return samples
        except Exception as exc:
            logger.warning("BigVul HuggingFace load failed (%s). Returning empty.", exc)
            return []

    def _row_to_sample(self, row: dict) -> VulnCodeSample:
        vuln_code = row.get("func_before") or row.get("func") or ""
        fixed_code = row.get("func_after") or None
        cwe = row.get("CWE ID") or row.get("cwe_id") or None
        desc = row.get("cve_desc") or row.get("summary") or ""
        cvss = float(row.get("CVSS Score", 0.0) or 0.0)
        severity = (
            "CRITICAL" if cvss >= 9.0
            else "HIGH" if cvss >= 7.0
            else "MEDIUM" if cvss >= 4.0
            else "LOW"
        )
        return VulnCodeSample(
            sample_id=str(row.get("CVE ID", row.get("id", ""))),
            source="bigvul",
            language="c_cpp",
            vulnerable_code=vuln_code,
            fixed_code=fixed_code,
            vulnerability_type=cwe or "unknown",
            cwe_id=cwe,
            description=desc,
            severity=severity,
            commit_url=row.get("commit_url") or row.get("commit_id"),
        )


# ── SWE-bench Loader ──────────────────────────────────────────────────────────

class SWEBenchLoader:
    """
    Loads the SWE-bench benchmark: real-world Python bugs from GitHub issues.
    Provides pairs of (buggy code, fixed code) with natural-language descriptions.
    Especially valuable for AI-generated code error patterns.
    Source: princeton-nlp/SWE-bench (HuggingFace)
    """

    HF_DATASET = "princeton-nlp/SWE-bench"

    def load(self, split: str = "test", max_samples: int = 2_000) -> list[VulnCodeSample]:
        try:
            ds_lib = _datasets()
            dataset = ds_lib.load_dataset(self.HF_DATASET, split=split, trust_remote_code=True)
            samples = []
            for i, row in enumerate(dataset):
                if i >= max_samples:
                    break
                samples.append(self._row_to_sample(row))
            return samples
        except Exception as exc:
            logger.warning("SWE-bench load failed (%s).", exc)
            return []

    def _row_to_sample(self, row: dict) -> VulnCodeSample:
        problem_stmt = row.get("problem_statement", "")
        patch = row.get("patch", "")
        # Extract before/after code from unified diff
        before_lines = [l[1:] for l in patch.split("\n") if l.startswith("-") and not l.startswith("---")]
        after_lines = [l[1:] for l in patch.split("\n") if l.startswith("+") and not l.startswith("+++")]

        return VulnCodeSample(
            sample_id=row.get("instance_id", ""),
            source="swebench",
            language="python",
            vulnerable_code="\n".join(before_lines),
            fixed_code="\n".join(after_lines),
            vulnerability_type="functional_bug",
            cwe_id=None,
            description=problem_stmt,
            severity="MEDIUM",
            commit_url=row.get("base_commit"),
        )


# ── CWE Catalog Loader ────────────────────────────────────────────────────────

class CWECatalogLoader:
    """
    Loads the MITRE CWE catalog.
    Primary: downloads JSON from cwe.mitre.org/data/
    Fallback: built-in CWE Top 25 (2024) embedded below.
    """

    CWE_JSON_URL = "https://cwe.mitre.org/data/json/699.json.zip"

    # CWE Top 25 (2024) — always available without network
    CWE_TOP25_2024: list[dict] = [
        {"id": "CWE-787", "name": "Out-of-bounds Write", "category": "Memory Safety",
         "desc": "Writing data past the end or before the beginning of an intended buffer."},
        {"id": "CWE-79",  "name": "Cross-site Scripting (XSS)", "category": "Injection",
         "desc": "Improper neutralization of user-controllable input in web page output."},
        {"id": "CWE-89",  "name": "SQL Injection", "category": "Injection",
         "desc": "Unsanitized input used in SQL query construction."},
        {"id": "CWE-416", "name": "Use After Free", "category": "Memory Safety",
         "desc": "Referencing memory after it has been freed."},
        {"id": "CWE-78",  "name": "OS Command Injection", "category": "Injection",
         "desc": "User-controlled input passed to OS command without sanitization."},
        {"id": "CWE-20",  "name": "Improper Input Validation", "category": "Validation",
         "desc": "Product does not validate or incorrectly validates input."},
        {"id": "CWE-125", "name": "Out-of-bounds Read", "category": "Memory Safety",
         "desc": "Reading data past the end or before the beginning of an intended buffer."},
        {"id": "CWE-22",  "name": "Path Traversal", "category": "Path Handling",
         "desc": "Allows attacker to access files outside intended directory."},
        {"id": "CWE-352", "name": "Cross-Site Request Forgery (CSRF)", "category": "Authentication",
         "desc": "Tricks victim into executing unwanted requests on authenticated web app."},
        {"id": "CWE-434", "name": "Unrestricted Upload of Dangerous File", "category": "File Handling",
         "desc": "Allows upload of files that can execute in the server context."},
        {"id": "CWE-502", "name": "Deserialization of Untrusted Data", "category": "Deserialization",
         "desc": "Deserializing untrusted data without verification."},
        {"id": "CWE-287", "name": "Improper Authentication", "category": "Authentication",
         "desc": "Failure to properly verify identity claims."},
        {"id": "CWE-476", "name": "NULL Pointer Dereference", "category": "Memory Safety",
         "desc": "Dereferencing a NULL pointer causes a crash."},
        {"id": "CWE-798", "name": "Hardcoded Credentials", "category": "Secrets",
         "desc": "Credentials embedded directly in source code."},
        {"id": "CWE-190", "name": "Integer Overflow", "category": "Numeric Errors",
         "desc": "Integer value wraps around due to overflow."},
        {"id": "CWE-306", "name": "Missing Authentication for Critical Function", "category": "Authentication",
         "desc": "Missing authentication allows unauthorized access to sensitive functionality."},
        {"id": "CWE-362", "name": "Race Condition", "category": "Concurrency",
         "desc": "Concurrent access to shared resource without synchronization."},
        {"id": "CWE-269", "name": "Improper Privilege Management", "category": "Authorization",
         "desc": "Application does not properly assign or revoke privileges."},
        {"id": "CWE-94",  "name": "Code Injection", "category": "Injection",
         "desc": "Attacker can inject code that is executed by the application."},
        {"id": "CWE-863", "name": "Incorrect Authorization", "category": "Authorization",
         "desc": "Access control check uses wrong actor or incorrect privilege."},
        {"id": "CWE-276", "name": "Incorrect Default Permissions", "category": "Permissions",
         "desc": "Default permissions are too broad."},
        {"id": "CWE-400", "name": "Uncontrolled Resource Consumption", "category": "Resource Management",
         "desc": "Resource consumption is not bounded, enabling DoS."},
        {"id": "CWE-119", "name": "Buffer Overflow (Generic)", "category": "Memory Safety",
         "desc": "Writing more data into a buffer than it can hold."},
        {"id": "CWE-918", "name": "Server-Side Request Forgery (SSRF)", "category": "SSRF",
         "desc": "Server makes requests to user-controlled URLs."},
        {"id": "CWE-77",  "name": "Command Injection (Generic)", "category": "Injection",
         "desc": "User input incorporated into a command without proper escaping."},
    ]

    def load_top25(self) -> list[CWEEntry]:
        entries = []
        for cwe in self.CWE_TOP25_2024:
            entries.append(CWEEntry(
                cwe_id=cwe["id"],
                name=cwe["name"],
                description=cwe["desc"],
                extended_description="",
                category=cwe["category"],
                likelihood="High",
                consequences=["Confidentiality", "Integrity", "Availability"],
                mitigations=["Input validation", "Parameterized APIs", "Principle of least privilege"],
                detection_methods=["SAST", "Code review", "Dynamic testing"],
                related_cwes=[],
            ))
        return entries

    async def load_full_catalog(self) -> list[CWEEntry]:
        """Attempt to download and parse the full CWE catalog JSON from MITRE."""
        import zipfile
        import io
        httpx = _httpx()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(self.CWE_JSON_URL)
                resp.raise_for_status()
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
                json_name = next((n for n in zf.namelist() if n.endswith(".json")), None)
                if not json_name:
                    return self.load_top25()
                data = json.loads(zf.read(json_name))
                return self._parse_catalog(data)
        except Exception as exc:
            logger.warning("Full CWE catalog download failed (%s). Using Top 25.", exc)
            return self.load_top25()

    def _parse_catalog(self, data: dict) -> list[CWEEntry]:
        entries = []
        weaknesses = data.get("Weakness_Catalog", {}).get("Weaknesses", {}).get("Weakness", [])
        for w in weaknesses[:500]:  # cap at 500 for memory
            cwe_id = f"CWE-{w.get('@ID', '')}"
            name = w.get("@Name", "")
            desc = w.get("Description", "")
            ext_desc = w.get("Extended_Description", "") or ""
            if isinstance(ext_desc, dict):
                ext_desc = str(ext_desc)
            entries.append(CWEEntry(
                cwe_id=cwe_id,
                name=name,
                description=desc,
                extended_description=ext_desc,
                category=w.get("@Abstraction", ""),
                likelihood=w.get("Likelihood_Of_Exploit", "Unknown"),
                consequences=[],
                mitigations=[],
                detection_methods=[],
                related_cwes=[],
            ))
        return entries


# ── GitHub Advisory Loader ────────────────────────────────────────────────────

class GitHubAdvisoryLoader:
    """
    Fetches security advisories from the GitHub Advisory Database (GHSA).
    Public API — no authentication required for basic queries.
    """

    BASE_URL = "https://api.github.com/advisories"

    def __init__(self, token: str | None = None):
        self.token = token
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def search(
        self,
        ecosystem: str | None = None,
        severity: str | None = None,
        cwe_id: str | None = None,
        per_page: int = 100,
    ) -> list[CVERecord]:
        params: dict[str, Any] = {"per_page": min(per_page, 100), "type": "reviewed"}
        if ecosystem:
            params["ecosystem"] = ecosystem
        if severity:
            params["severity"] = severity.lower()
        if cwe_id:
            params["cwe_id"] = cwe_id

        url = f"{self.BASE_URL}?{urlencode(params)}"
        httpx = _httpx()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=self._headers)
                resp.raise_for_status()
                advisories = resp.json()
        except Exception as exc:
            logger.warning("GitHub Advisory API error: %s", exc)
            return []

        records = []
        for adv in advisories:
            try:
                records.append(self._parse_advisory(adv))
            except Exception:
                continue
        return records

    def _parse_advisory(self, adv: dict) -> CVERecord:
        sev_map = {"critical": "CRITICAL", "high": "HIGH", "moderate": "MEDIUM", "low": "LOW"}
        severity = sev_map.get(adv.get("severity", "").lower(), "NONE")
        cvss = adv.get("cvss", {})
        cvss_score = float(cvss.get("score", 0.0) if cvss else 0.0)
        cwe_ids = [c.get("cwe_id", "") for c in (adv.get("cwes") or [])]
        return CVERecord(
            cve_id=adv.get("cve_id") or adv.get("ghsa_id", ""),
            description=adv.get("description") or adv.get("summary", ""),
            published=adv.get("published_at", ""),
            severity=severity,
            cvss_score=cvss_score,
            cwe_ids=cwe_ids,
            references=[adv.get("html_url", "")],
            affected_products=[
                f"{p.get('package', {}).get('ecosystem', '')}:{p.get('package', {}).get('name', '')}"
                for p in (adv.get("vulnerabilities") or [])
            ],
        )


# ── OWASP Knowledge Base ──────────────────────────────────────────────────────

class OWASPKnowledgeBase:
    """
    Built-in OWASP knowledge base.
    Includes OWASP Top 10 (2021) and OWASP LLM Top 10 (2025).
    Always available offline — no network required.
    """

    OWASP_TOP10_2021 = [
        {
            "id": "A01:2021",
            "name": "Broken Access Control",
            "description": "Restrictions on authenticated users are not properly enforced. Attackers can access unauthorized functionality or data.",
            "cwe_ids": ["CWE-200", "CWE-201", "CWE-352"],
            "fix_pattern": "Implement deny-by-default access control. Use server-side authorization checks. Log and alert on access control failures.",
            "examples": ["IDOR", "Privilege escalation", "JWT tampering", "CORS misconfiguration"],
        },
        {
            "id": "A02:2021",
            "name": "Cryptographic Failures",
            "description": "Failures related to cryptography or lack thereof, exposing sensitive data in transit or at rest.",
            "cwe_ids": ["CWE-259", "CWE-327", "CWE-331"],
            "fix_pattern": "Use TLS 1.2+ for data in transit. Encrypt sensitive data at rest. Use strong algorithms (AES-256, bcrypt). Never use MD5/SHA1 for passwords.",
            "examples": ["Cleartext passwords", "Weak cipher", "Hardcoded keys", "Insecure random"],
        },
        {
            "id": "A03:2021",
            "name": "Injection",
            "description": "Hostile data sent to an interpreter as part of a command or query can trick it into executing unintended commands.",
            "cwe_ids": ["CWE-89", "CWE-78", "CWE-79"],
            "fix_pattern": "Use parameterized queries. Validate and sanitize all input. Apply positive allowlist input validation. Use ORMs that handle escaping.",
            "examples": ["SQL injection", "Command injection", "XSS", "LDAP injection"],
        },
        {
            "id": "A04:2021",
            "name": "Insecure Design",
            "description": "Missing or ineffective security controls at the design level. Distinct from implementation bugs.",
            "cwe_ids": ["CWE-209", "CWE-256", "CWE-501"],
            "fix_pattern": "Threat modeling during design. Security user stories. Reference architectures. Segregate tiers. Limit resource consumption by user/IP.",
            "examples": ["No rate limiting", "Business logic flaws", "Missing anti-CSRF"],
        },
        {
            "id": "A05:2021",
            "name": "Security Misconfiguration",
            "description": "Missing appropriate security hardening across any part of the application stack.",
            "cwe_ids": ["CWE-2", "CWE-16", "CWE-388"],
            "fix_pattern": "Repeatable hardening processes. Minimal platform with no unnecessary features. Review defaults. Automated config verification in CI/CD.",
            "examples": ["Default credentials", "Overly permissive CORS", "Verbose error messages", "Debug mode on"],
        },
        {
            "id": "A06:2021",
            "name": "Vulnerable and Outdated Components",
            "description": "Components with known vulnerabilities used without patching.",
            "cwe_ids": ["CWE-1035", "CWE-937"],
            "fix_pattern": "Subscribe to vulnerability notifications. Continuously inventory components and versions. Remove unused dependencies. Pin versions in lock files.",
            "examples": ["Outdated libraries", "Unpatched OS", "Abandoned packages"],
        },
        {
            "id": "A07:2021",
            "name": "Identification and Authentication Failures",
            "description": "Weaknesses in authentication and session management allowing attackers to assume other users' identities.",
            "cwe_ids": ["CWE-287", "CWE-384", "CWE-620"],
            "fix_pattern": "Multi-factor authentication. No default credentials. Weak password checks. Limit failed login attempts. Invalidate sessions on logout.",
            "examples": ["Credential stuffing", "Brute force", "Weak passwords", "Session fixation"],
        },
        {
            "id": "A08:2021",
            "name": "Software and Data Integrity Failures",
            "description": "Code and infrastructure failures related to integrity verification of software updates, critical data, and CI/CD pipelines.",
            "cwe_ids": ["CWE-502", "CWE-829"],
            "fix_pattern": "Verify digital signatures on software. Use trusted repos. Ensure CI/CD pipeline integrity. Use serialization libraries that reject hostile objects.",
            "examples": ["Insecure deserialization", "Unsigned updates", "Compromised dependencies"],
        },
        {
            "id": "A09:2021",
            "name": "Security Logging and Monitoring Failures",
            "description": "Insufficient logging and monitoring allows attackers to achieve goals undetected.",
            "cwe_ids": ["CWE-778", "CWE-223"],
            "fix_pattern": "Log authentication, access control failures. Ensure logs are in a format that monitoring tools can consume. Establish incident response plans.",
            "examples": ["No audit logs", "Logs not monitored", "Logs stored locally only"],
        },
        {
            "id": "A10:2021",
            "name": "Server-Side Request Forgery (SSRF)",
            "description": "Web app fetches a remote resource based on user-supplied URL without validating it.",
            "cwe_ids": ["CWE-918"],
            "fix_pattern": "Validate and sanitize all client-supplied input data. Enforce URL schema, port, and destination with a positive allowlist. Disable HTTP redirections.",
            "examples": ["Cloud metadata access", "Internal port scanning", "File:// URI", "Blind SSRF"],
        },
    ]

    OWASP_LLM_TOP10_2025 = [
        {
            "id": "LLM01:2025",
            "name": "Prompt Injection",
            "description": "Attacker crafts inputs that override LLM instructions or manipulate its behavior.",
            "cwe_ids": ["CWE-74"],
            "fix_pattern": "Separate instruction and data channels. Use structured prompt formats. Apply input/output filtering. Implement privilege controls on LLM actions.",
        },
        {
            "id": "LLM02:2025",
            "name": "Sensitive Information Disclosure",
            "description": "LLM inadvertently reveals confidential data from training data or system prompts.",
            "cwe_ids": ["CWE-200"],
            "fix_pattern": "Sanitize training data. Apply output filtering. Implement strict access controls. Monitor for data leakage patterns.",
        },
        {
            "id": "LLM03:2025",
            "name": "Supply Chain Vulnerabilities",
            "description": "Vulnerabilities in pre-trained models, datasets, or third-party integrations.",
            "cwe_ids": ["CWE-1357"],
            "fix_pattern": "Verify model provenance. Audit third-party packages. Monitor model behavior post-deployment. Pin model versions.",
        },
        {
            "id": "LLM04:2025",
            "name": "Data and Model Poisoning",
            "description": "Manipulation of training data or fine-tuning processes to introduce backdoors or biases.",
            "cwe_ids": ["CWE-20"],
            "fix_pattern": "Validate training data integrity. Use differential privacy. Monitor model outputs for anomalies. Red-team fine-tuning processes.",
        },
        {
            "id": "LLM05:2025",
            "name": "Improper Output Handling",
            "description": "LLM output passed to downstream components without validation.",
            "cwe_ids": ["CWE-116"],
            "fix_pattern": "Treat LLM output as untrusted. Apply output encoding. Validate structure and content. Apply standard injection prevention.",
        },
        {
            "id": "LLM06:2025",
            "name": "Excessive Agency",
            "description": "LLM-based system performs actions with too broad scope or permissions.",
            "cwe_ids": ["CWE-272"],
            "fix_pattern": "Apply least privilege to LLM-invokable tools. Require human-in-the-loop for high-impact actions. Audit all agent actions.",
        },
        {
            "id": "LLM07:2025",
            "name": "System Prompt Leakage",
            "description": "Confidential system prompt extracted through adversarial queries.",
            "cwe_ids": ["CWE-200"],
            "fix_pattern": "Treat system prompts as untrusted if they contain secrets. Monitor for extraction attempts. Use structural separation.",
        },
        {
            "id": "LLM08:2025",
            "name": "Vector and Embedding Weaknesses",
            "description": "Embedding space manipulated for adversarial retrieval or data reconstruction.",
            "cwe_ids": ["CWE-922"],
            "fix_pattern": "Access control on vector databases. Monitor retrieval queries. Apply data minimization. Encrypt embeddings at rest.",
        },
        {
            "id": "LLM09:2025",
            "name": "Misinformation",
            "description": "LLM produces plausible but factually incorrect outputs used in high-stakes decisions.",
            "cwe_ids": ["CWE-20"],
            "fix_pattern": "Ground LLM in verified sources (RAG). Apply fact-checking. Communicate uncertainty. Human review for high-stakes decisions.",
        },
        {
            "id": "LLM10:2025",
            "name": "Unbounded Consumption",
            "description": "LLM resource consumption not limited, enabling DoS or excessive cost.",
            "cwe_ids": ["CWE-400"],
            "fix_pattern": "Rate limiting per user/IP. Input length limits. Budget alerts. Auto-scaling caps. Fallback responses under load.",
        },
    ]

    def get_owasp_top10(self) -> list[dict]:
        return self.OWASP_TOP10_2021

    def get_llm_top10(self) -> list[dict]:
        return self.OWASP_LLM_TOP10_2025

    def get_all_entries(self) -> list[dict]:
        return self.OWASP_TOP10_2021 + self.OWASP_LLM_TOP10_2025

    def find_by_category(self, category_name: str) -> dict | None:
        all_entries = self.get_all_entries()
        lower = category_name.lower()
        for entry in all_entries:
            if lower in entry["name"].lower() or lower in entry["id"].lower():
                return entry
        return None

    def find_by_cwe(self, cwe_id: str) -> list[dict]:
        return [
            e for e in self.get_all_entries()
            if cwe_id in e.get("cwe_ids", [])
        ]
