"""Daily SEDUC rules crawler.

Fetches pedagogical guidelines from official São Paulo education portals
every day at 06:00 (configurable) and ingests new content into the
knowledge base so MS-006 always has up-to-date SEDUC context.

Sources are driven by SEDUC_CRAWLER_SOURCES env var (JSON list of objects):
  [{"name": "...", "url": "...", "selector": "article", "type": "seduc_policy"}]

Defaults include the standard SEDUC/EFAPE portals if no env var is set.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup

from app.application.use_cases.ingest_document import IngestDocumentUseCase, IngestInput
from app.database import SessionLocal
from app.domain.knowledge import DocumentType
from app.models.crawl_log import CrawlLogModel
from app.models.document import DocumentChunkModel, KnowledgeDocumentModel
from app.config import settings

logger = logging.getLogger(__name__)

_ingest = IngestDocumentUseCase()

# ── Default SEDUC source list ─────────────────────────────────────────────────

_DEFAULT_SOURCES: list[dict] = [
    {
        "name":     "EFAPE Notícias",
        "url":      "https://efape.educacao.sp.gov.br/noticias/",
        "selector": "article",
        "type":     "seduc_policy",
        "index_only": True,   # only fetch linked articles from index page
    },
    {
        "name":     "SEDUC Comunicados",
        "url":      "https://www.educacao.sp.gov.br/noticias/",
        "selector": "article",
        "type":     "seduc_policy",
        "index_only": True,
    },
    {
        "name":     "Currículo Paulista — EFAPE",
        "url":      "https://efape.educacao.sp.gov.br/curriculopaulista/",
        "selector": "main",
        "type":     "curriculum_guide",
        "index_only": False,
    },
]


def _load_sources() -> list[dict]:
    raw = getattr(settings, "SEDUC_CRAWLER_SOURCES", "")
    if raw and raw.strip():
        try:
            return json.loads(raw)
        except Exception:
            logger.warning("SEDUC_CRAWLER_SOURCES is not valid JSON — using defaults")
    return _DEFAULT_SOURCES


# ── URL hash ──────────────────────────────────────────────────────────────────

def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:64]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_text(url: str, selector: str = "body") -> Optional[tuple[str, str]]:
    """Return (title, body_text) or None on failure."""
    try:
        resp = httpx.get(url, timeout=20.0, follow_redirects=True,
                         headers={"User-Agent": "PEC-SEDUC-Crawler/1.0 (+educacao.sp.gov.br)"})
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title") or soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else url

        container = soup.select_one(selector) or soup.find("body")
        if not container:
            return None

        # Remove navigation / footer noise
        for tag in container.select("nav, footer, script, style, aside"):
            tag.decompose()

        text = container.get_text(separator="\n", strip=True)
        if len(text) < 100:
            return None
        return title, text
    except Exception as exc:
        logger.debug("Fetch failed %s: %s", url, exc)
        return None


def _collect_article_links(index_url: str, selector: str) -> list[str]:
    """From an index/listing page, return all <a href> inside `selector` elements."""
    try:
        resp = httpx.get(index_url, timeout=20.0, follow_redirects=True,
                         headers={"User-Agent": "PEC-SEDUC-Crawler/1.0"})
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        base = index_url.rstrip("/")
        links: list[str] = []
        for el in soup.select(selector):
            for a in el.select("a[href]"):
                href = a["href"]
                if href.startswith("http"):
                    links.append(href)
                elif href.startswith("/"):
                    # Reconstruct absolute URL from base domain
                    from urllib.parse import urlparse
                    parsed = urlparse(index_url)
                    links.append(f"{parsed.scheme}://{parsed.netloc}{href}")
        return list(dict.fromkeys(links))  # deduplicate preserving order
    except Exception as exc:
        logger.debug("Link collection failed %s: %s", index_url, exc)
        return []


def _already_crawled(db, url_hash: str) -> bool:
    return db.query(CrawlLogModel).filter_by(url_hash=url_hash, success=True).first() is not None


def _log_crawl(db, url: str, source: str, success: bool,
               title: Optional[str] = None, doc_id: Optional[str] = None,
               error_msg: Optional[str] = None) -> None:
    entry = CrawlLogModel(
        url_hash   = _hash(url),
        url        = url,
        source     = source,
        title      = title,
        doc_id     = doc_id,
        success    = success,
        error_msg  = error_msg,
        crawled_at = datetime.now(timezone.utc),
    )
    db.merge(entry)   # upsert — url_hash is unique
    db.commit()


# ── Core crawl logic ──────────────────────────────────────────────────────────

def _ingest_url(db, url: str, source: dict) -> Optional[str]:
    """Fetch url, extract text, ingest into knowledge base. Returns doc_id or None."""
    result = _fetch_text(url, source.get("selector", "main"))
    if not result:
        _log_crawl(db, url, source["name"], success=False, error_msg="No content extracted")
        return None

    title, text = result
    doc_type_str = source.get("type", "seduc_policy")
    try:
        doc_type = DocumentType(doc_type_str)
    except ValueError:
        doc_type = DocumentType.SEDUC_POLICY

    try:
        doc = _ingest.execute(IngestInput(
            title           = f"[SEDUC Auto] {title}",
            document_type   = doc_type,
            source_filename = url,
            raw_bytes       = text.encode("utf-8"),
            content_type    = "text/plain",
            uploaded_by     = "seduc-crawler",
            description     = f"Capturado automaticamente de {source['name']} em "
                              f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        ))
    except ValueError as exc:
        _log_crawl(db, url, source["name"], success=False, error_msg=str(exc))
        return None

    db_doc = KnowledgeDocumentModel(
        id              = doc.id,
        title           = doc.title,
        document_type   = doc.document_type.value,
        source_filename = doc.source_filename,
        description     = doc.description,
        full_text       = doc.full_text,
        chunk_count     = doc.chunk_count,
        uploaded_by     = doc.uploaded_by,
        is_active       = True,
    )
    db.add(db_doc)
    for chunk in doc.chunks:
        db.add(DocumentChunkModel(
            document_id = doc.id,
            chunk_index = chunk.chunk_index,
            text        = chunk.text,
            char_start  = chunk.char_start,
            char_end    = chunk.char_end,
        ))
    db.commit()

    _log_crawl(db, url, source["name"], success=True, title=title, doc_id=doc.id)
    logger.info("Ingested '%s' from %s (doc=%s, %d chunks)", title, source["name"], doc.id, doc.chunk_count)
    return doc.id


def run_crawl() -> dict:
    """Execute one full crawl cycle across all sources. Returns a summary dict."""
    sources = _load_sources()
    db = SessionLocal()
    total_new = 0
    total_skip = 0
    total_fail = 0

    try:
        for source in sources:
            index_url = source["url"]
            index_only = source.get("index_only", False)

            if index_only:
                urls = _collect_article_links(index_url, source.get("selector", "article"))
                if not urls:
                    logger.warning("No article links found on %s", index_url)
                    continue
            else:
                urls = [index_url]

            for url in urls[:20]:  # max 20 per source per day to be polite
                h = _hash(url)
                if _already_crawled(db, h):
                    total_skip += 1
                    continue

                doc_id = _ingest_url(db, url, source)
                if doc_id:
                    total_new += 1
                else:
                    total_fail += 1

    except Exception as exc:
        logger.error("Crawl cycle failed: %s", exc)
    finally:
        db.close()

    summary = {"new": total_new, "skipped": total_skip, "failed": total_fail}
    logger.info("SEDUC crawl complete: %s", summary)
    return summary


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

_scheduler: BackgroundScheduler | None = None


def start_scheduler(run_hour: int = 6, run_minute: int = 0) -> None:
    """Start the daily crawl scheduler. Runs at run_hour:run_minute every day."""
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    _scheduler.add_job(
        func   = run_crawl,
        trigger = "cron",
        hour   = run_hour,
        minute = run_minute,
        id     = "seduc_daily_crawl",
        replace_existing = True,
    )
    _scheduler.start()
    logger.info("SEDUC daily crawler scheduled at %02d:%02d (America/Sao_Paulo)", run_hour, run_minute)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
