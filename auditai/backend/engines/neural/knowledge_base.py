"""
Vulnerability Knowledge Base
============================
A persisted vector store that holds embeddings for:
  • CVE/GHSA vulnerability descriptions (from NVD + GitHub Advisories)
  • CWE entries (from MITRE catalog)
  • OWASP guidance (Top 10 + LLM Top 10)
  • Academic techniques (from arXiv papers)
  • Fix patterns (before/after code pairs)

Storage: JSON file for metadata + numpy .npy for embedding matrix.
Search: cosine similarity (sklearn NearestNeighbors, brute-force for ≤10k entries;
        switches to Ball-tree for larger sets).

Lifecycle:
  kb = VulnerabilityKnowledgeBase(persist_path="./data/vuln_kb")
  await kb.ingest_nvd(nvd_connector, keyword="injection")
  await kb.ingest_cwe(cwe_loader)
  await kb.ingest_arxiv(arxiv_connector)
  results = kb.search("SQL injection in web API", top_k=5)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class KBEntry:
    entry_id: str
    source: str          # nvd | cwe | owasp | arxiv | fix_pattern | ghsa
    entry_type: str      # vulnerability | technique | fix | guideline
    title: str
    description: str
    metadata: dict       # source-specific fields (cve_id, url, cwe_ids, ...)
    created_at: float = field(default_factory=time.time)


class VulnerabilityKnowledgeBase:
    """
    Semantic knowledge base with persistence.

    Methods
    -------
    ingest_* :  add entries from a specific data source
    search   :  semantic similarity search returning KBEntry list
    search_techniques : search returning TechniqueMatch list (for TechniqueRetriever)
    keyword_search_techniques : regex/substring fallback
    add_entry : add a single entry with pre-computed embedding
    save / load : persist to / restore from disk
    """

    META_FILE = "kb_meta.json"
    EMB_FILE = "kb_embeddings.npy"
    DEFAULT_EMBED_DIM = 384   # all-MiniLM-L6-v2

    def __init__(
        self,
        persist_path: str | None = None,
        embedder=None,         # sentence_transformers.SentenceTransformer or None
        embed_dim: int = DEFAULT_EMBED_DIM,
    ):
        self._path = Path(persist_path) if persist_path else None
        self._embedder = embedder
        self._embed_dim = embed_dim
        self._entries: list[KBEntry] = []
        self._embeddings: np.ndarray = np.empty((0, embed_dim), dtype=np.float32)
        self._index = None          # sklearn NearestNeighbors, built lazily

        if self._path and self._path.exists():
            self._load()

    # ── Embedding helper ──────────────────────────────────────────────────────

    def _embed(self, text: str) -> np.ndarray | None:
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                return None
        try:
            v = self._embedder.encode(text, normalize_embeddings=True)
            return v.astype(np.float32)
        except Exception as exc:
            logger.warning("Embedding error: %s", exc)
            return None

    def _invalidate_index(self) -> None:
        self._index = None

    def _build_index(self) -> None:
        if len(self._entries) == 0:
            return
        try:
            from sklearn.neighbors import NearestNeighbors
            algo = "ball_tree" if len(self._entries) > 10_000 else "brute"
            self._index = NearestNeighbors(
                n_neighbors=min(20, len(self._entries)),
                metric="cosine",
                algorithm=algo,
            ).fit(self._embeddings)
        except Exception as exc:
            logger.warning("Index build error: %s", exc)
            self._index = None

    # ── Core add/search ───────────────────────────────────────────────────────

    def add_entry(self, entry: KBEntry, embedding: np.ndarray | None = None) -> None:
        """Add a single entry. Embeds the title+description if embedding not provided."""
        if embedding is None:
            text = f"{entry.title}. {entry.description}"
            embedding = self._embed(text)

        if embedding is None:
            # No embedder available — store entry without embedding (keyword search only)
            self._entries.append(entry)
            zero = np.zeros((1, self._embed_dim), dtype=np.float32)
            self._embeddings = np.vstack([self._embeddings, zero])
        else:
            self._entries.append(entry)
            emb2d = embedding.reshape(1, -1).astype(np.float32)
            self._embeddings = np.vstack([self._embeddings, emb2d])

        self._invalidate_index()

    def search(self, query: str, top_k: int = 5) -> list[tuple[KBEntry, float]]:
        """
        Semantic search. Returns list of (entry, similarity_score) tuples,
        sorted by descending similarity.
        """
        if len(self._entries) == 0:
            return []

        q_emb = self._embed(query)
        if q_emb is None:
            return self.keyword_search(query, top_k)

        if self._index is None:
            self._build_index()

        if self._index is None:
            return self._cosine_search(q_emb, top_k)

        try:
            q2d = q_emb.reshape(1, -1)
            distances, indices = self._index.kneighbors(q2d, n_neighbors=min(top_k, len(self._entries)))
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                similarity = float(1.0 - dist)   # cosine distance → similarity
                results.append((self._entries[idx], similarity))
            return results
        except Exception as exc:
            logger.warning("Index search error: %s", exc)
            return self._cosine_search(q_emb, top_k)

    def _cosine_search(self, q_emb: np.ndarray, top_k: int) -> list[tuple[KBEntry, float]]:
        """Brute-force cosine similarity fallback."""
        if self._embeddings.shape[0] == 0:
            return []
        sims = (self._embeddings @ q_emb).tolist()
        ranked = sorted(enumerate(sims), key=lambda x: -x[1])[:top_k]
        return [(self._entries[i], float(s)) for i, s in ranked]

    def keyword_search(self, query: str, top_k: int = 5) -> list[tuple[KBEntry, float]]:
        """Substring keyword fallback when no embedder is available."""
        lower = query.lower()
        scored = []
        for entry in self._entries:
            score = 0.0
            text = f"{entry.title} {entry.description}".lower()
            for word in lower.split():
                if word in text:
                    score += 1.0 / len(lower.split())
            if score > 0:
                scored.append((entry, score))
        return sorted(scored, key=lambda x: -x[1])[:top_k]

    # ── TechniqueRetriever interface ──────────────────────────────────────────

    def search_techniques(self, q_emb, top_k: int = 5):
        from .models import TechniqueMatch
        results = self._cosine_search(q_emb, top_k)
        matches = []
        for entry, sim in results:
            matches.append(TechniqueMatch(
                source=entry.entry_id,
                title=entry.title,
                description=entry.description,
                similarity=sim,
                fix_techniques=entry.metadata.get("fix_techniques", []),
                url=entry.metadata.get("url"),
            ))
        return matches

    def keyword_search_techniques(self, query: str, top_k: int = 5):
        from .models import TechniqueMatch
        results = self.keyword_search(query, top_k)
        return [
            TechniqueMatch(
                source=e.entry_id,
                title=e.title,
                description=e.description,
                similarity=sim,
                fix_techniques=e.metadata.get("fix_techniques", []),
                url=e.metadata.get("url"),
            )
            for e, sim in results
        ]

    # ── Bulk ingestion ────────────────────────────────────────────────────────

    async def ingest_nvd(
        self,
        nvd_connector,
        keyword: str = "injection",
        max_results: int = 200,
    ) -> int:
        """Ingest CVE records from NVD into the knowledge base."""
        records = await nvd_connector.search(keyword=keyword, results_per_page=max_results)
        added = 0
        for rec in records:
            entry = KBEntry(
                entry_id=f"nvd:{rec.cve_id}",
                source="nvd",
                entry_type="vulnerability",
                title=rec.cve_id,
                description=rec.description,
                metadata={
                    "cve_id": rec.cve_id,
                    "severity": rec.severity,
                    "cvss_score": rec.cvss_score,
                    "cwe_ids": rec.cwe_ids,
                    "published": rec.published,
                    "references": rec.references[:3],
                },
            )
            if not self._duplicate(entry.entry_id):
                self.add_entry(entry)
                added += 1
        logger.info("Ingested %d NVD CVE records (keyword=%s)", added, keyword)
        return added

    async def ingest_arxiv(
        self,
        arxiv_connector,
        query: str = "vulnerability detection deep learning",
        max_results: int = 100,
    ) -> int:
        """Ingest arXiv papers into the knowledge base."""
        papers = await arxiv_connector.search(query=query, max_results=max_results)
        added = 0
        for paper in papers:
            entry = KBEntry(
                entry_id=f"arxiv:{paper.arxiv_id}",
                source="arxiv",
                entry_type="technique",
                title=paper.title,
                description=paper.abstract,
                metadata={
                    "arxiv_id": paper.arxiv_id,
                    "authors": paper.authors[:3],
                    "published": paper.published,
                    "categories": paper.categories,
                    "url": paper.url,
                    "fix_techniques": paper.fix_techniques,
                },
            )
            if not self._duplicate(entry.entry_id):
                self.add_entry(entry)
                added += 1
        logger.info("Ingested %d arXiv papers (query=%s)", added, query)
        return added

    def ingest_cwe(self, cwe_loader) -> int:
        """Ingest CWE catalog entries."""
        entries = cwe_loader.load_top25()
        added = 0
        for cwe in entries:
            entry = KBEntry(
                entry_id=f"cwe:{cwe.cwe_id}",
                source="cwe",
                entry_type="guideline",
                title=f"{cwe.cwe_id}: {cwe.name}",
                description=f"{cwe.description} {cwe.extended_description}".strip(),
                metadata={
                    "cwe_id": cwe.cwe_id,
                    "category": cwe.category,
                    "likelihood": cwe.likelihood,
                    "mitigations": cwe.mitigations,
                    "fix_techniques": cwe.mitigations,
                },
            )
            if not self._duplicate(entry.entry_id):
                self.add_entry(entry)
                added += 1
        logger.info("Ingested %d CWE entries", added)
        return added

    def ingest_owasp(self, owasp_kb) -> int:
        """Ingest OWASP Top 10 and LLM Top 10 entries."""
        added = 0
        for item in owasp_kb.get_all_entries():
            entry = KBEntry(
                entry_id=f"owasp:{item['id']}",
                source="owasp",
                entry_type="guideline",
                title=f"{item['id']}: {item['name']}",
                description=item["description"],
                metadata={
                    "owasp_id": item["id"],
                    "cwe_ids": item.get("cwe_ids", []),
                    "fix_pattern": item.get("fix_pattern", ""),
                    "fix_techniques": [item.get("fix_pattern", "")],
                    "examples": item.get("examples", []),
                },
            )
            if not self._duplicate(entry.entry_id):
                self.add_entry(entry)
                added += 1
        logger.info("Ingested %d OWASP entries", added)
        return added

    def add_fix_pattern(
        self,
        fix_id: str,
        vuln_description: str,
        before_code: str,
        after_code: str,
        cwe_id: str | None = None,
        source: str = "manual",
    ) -> None:
        """Add a vulnerability/fix code pair to the knowledge base."""
        text = f"Fix for: {vuln_description}. Before: {before_code[:300]} After: {after_code[:300]}"
        entry = KBEntry(
            entry_id=f"fix:{fix_id}",
            source=source,
            entry_type="fix",
            title=f"Fix: {vuln_description[:100]}",
            description=text,
            metadata={
                "before_code": before_code,
                "after_code": after_code,
                "cwe_id": cwe_id,
                "fix_techniques": ["code_transformation"],
            },
        )
        if not self._duplicate(entry.entry_id):
            self.add_entry(entry)

    # ── Statistics ────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for e in self._entries:
            by_source[e.source] = by_source.get(e.source, 0) + 1
            by_type[e.entry_type] = by_type.get(e.entry_type, 0) + 1
        return {
            "total_entries": len(self._entries),
            "embedding_shape": list(self._embeddings.shape),
            "by_source": by_source,
            "by_type": by_type,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        if self._path is None:
            return
        self._path.mkdir(parents=True, exist_ok=True)
        meta_path = self._path / self.META_FILE
        emb_path = self._path / self.EMB_FILE
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self._entries], f, default=str)
        np.save(str(emb_path), self._embeddings)
        logger.info(
            "Saved knowledge base: %d entries → %s", len(self._entries), self._path
        )

    def _load(self) -> None:
        meta_path = self._path / self.META_FILE
        emb_path = self._path / self.EMB_FILE
        if not meta_path.exists():
            return
        try:
            with open(meta_path, encoding="utf-8") as f:
                raw = json.load(f)
            self._entries = [KBEntry(**r) for r in raw]
            if emb_path.exists():
                self._embeddings = np.load(str(emb_path)).astype(np.float32)
            else:
                self._embeddings = np.zeros(
                    (len(self._entries), self._embed_dim), dtype=np.float32
                )
            logger.info("Loaded knowledge base: %d entries from %s", len(self._entries), self._path)
        except Exception as exc:
            logger.warning("Knowledge base load error: %s", exc)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _duplicate(self, entry_id: str) -> bool:
        return any(e.entry_id == entry_id for e in self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"<VulnerabilityKnowledgeBase entries={len(self._entries)} path={self._path}>"
