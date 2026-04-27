"""Ingest a document: extract text, chunk, persist."""
import io
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.knowledge import DocumentChunk, DocumentType, KnowledgeDocument

CHUNK_SIZE = 600       # chars per chunk
CHUNK_OVERLAP = 80     # overlap between consecutive chunks


@dataclass
class IngestInput:
    title: str
    document_type: DocumentType
    source_filename: str
    raw_bytes: bytes
    content_type: str
    uploaded_by: str
    description: Optional[str] = None


def _extract_text(raw_bytes: bytes, content_type: str) -> str:
    """Extract plain text from PDF or text/plain content."""
    if "pdf" in content_type.lower():
        try:
            from pdfminer.high_level import extract_text as pdf_extract
            return pdf_extract(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise ValueError(f"PDF extraction failed: {exc}") from exc
    # Plain text / markdown
    return raw_bytes.decode("utf-8", errors="replace")


def _chunk_text(text: str) -> list[DocumentChunk]:
    """Split text into overlapping chunks for retrieval."""
    chunks: list[DocumentChunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(DocumentChunk(
                chunk_index=idx,
                text=chunk_text,
                char_start=start,
                char_end=end,
            ))
            idx += 1
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return chunks


class IngestDocumentUseCase:
    def execute(self, inp: IngestInput) -> KnowledgeDocument:
        full_text = _extract_text(inp.raw_bytes, inp.content_type)
        if not full_text.strip():
            raise ValueError("Document produced no extractable text")

        chunks = _chunk_text(full_text)
        doc_id = str(uuid.uuid4())

        return KnowledgeDocument(
            id              = doc_id,
            title           = inp.title,
            document_type   = inp.document_type,
            source_filename = inp.source_filename,
            full_text       = full_text,
            chunks          = chunks,
            chunk_count     = len(chunks),
            uploaded_by     = inp.uploaded_by,
            is_active       = True,
            created_at      = datetime.now(tz=timezone.utc),
            description     = inp.description,
        )
