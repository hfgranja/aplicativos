"""
RAG (Retrieval-Augmented Generation) quality check.
Validates retrieval relevance and answer grounding for RAG applications.
"""
import re
from typing import List
from engines.base import FindingData


def run(context: dict) -> List[FindingData]:
    """
    Checks RAG pipeline quality.
    context keys:
      - rag_samples: list of {"query": str, "retrieved_docs": list[str], "answer": str}
      - source_code: str  (fallback — detect RAG patterns without grounding checks)
    """
    findings = []
    samples = context.get("rag_samples", [])

    if samples:
        for i, sample in enumerate(samples):
            query = sample.get("query", "")
            docs = sample.get("retrieved_docs", [])
            answer = sample.get("answer", "")

            if not answer:
                continue

            # Check 1: Answer grounding — key terms in answer should appear in retrieved docs
            if docs:
                answer_tokens = set(re.findall(r'\b\w{5,}\b', answer.lower()))
                doc_text = " ".join(docs).lower()
                doc_tokens = set(re.findall(r'\b\w{5,}\b', doc_text))
                ungrounded = answer_tokens - doc_tokens
                grounding_ratio = 1 - (len(ungrounded) / max(len(answer_tokens), 1))

                if grounding_ratio < 0.5:
                    findings.append(FindingData(
                        engine="ai_evals",
                        severity="HIGH",
                        category="ai_evals.rag_quality",
                        title="Low answer grounding — response not supported by retrieved documents",
                        description=(
                            f"Sample {i + 1}: Only {grounding_ratio:.0%} of answer terms appear "
                            f"in the retrieved documents. The model may be hallucinating facts "
                            f"not present in the knowledge base."
                        ),
                        evidence={
                            "sample_index": i,
                            "query": query[:200],
                            "grounding_ratio": round(grounding_ratio, 3),
                            "ungrounded_terms_sample": list(ungrounded)[:10],
                        },
                        pyramid_level=11,
                    ))
                elif grounding_ratio < 0.7:
                    findings.append(FindingData(
                        engine="ai_evals",
                        severity="MEDIUM",
                        category="ai_evals.rag_quality",
                        title="Partial answer grounding — some unverified claims",
                        description=(
                            f"Sample {i + 1}: {grounding_ratio:.0%} of answer terms are grounded "
                            f"in retrieved documents. Review ungrounded claims for accuracy."
                        ),
                        evidence={
                            "sample_index": i,
                            "grounding_ratio": round(grounding_ratio, 3),
                        },
                        pyramid_level=11,
                    ))

            # Check 2: Retrieval relevance — query terms should appear in retrieved docs
            if docs:
                query_tokens = set(re.findall(r'\b\w{4,}\b', query.lower()))
                stop_words = {"what", "when", "where", "which", "this", "that", "with", "from"}
                query_tokens -= stop_words
                doc_text = " ".join(docs).lower()
                relevant = sum(1 for t in query_tokens if t in doc_text)
                relevance_ratio = relevant / max(len(query_tokens), 1)

                if relevance_ratio < 0.4 and len(docs) > 0:
                    findings.append(FindingData(
                        engine="ai_evals",
                        severity="MEDIUM",
                        category="ai_evals.rag_quality",
                        title="Low retrieval relevance — documents may not match query",
                        description=(
                            f"Sample {i + 1}: Retrieved documents cover only {relevance_ratio:.0%} "
                            f"of the query's key terms. The retriever may be returning irrelevant chunks, "
                            f"leading to poor answer quality."
                        ),
                        evidence={
                            "sample_index": i,
                            "query": query[:200],
                            "relevance_ratio": round(relevance_ratio, 3),
                            "num_docs": len(docs),
                        },
                        pyramid_level=11,
                    ))
    else:
        # Static analysis fallback — detect RAG setups without grounding validation
        source = context.get("source_code", "")
        if source:
            _static_rag_check(source, findings)

    return findings


def _static_rag_check(source: str, findings: List[FindingData]) -> None:
    """Detect RAG patterns in code that lack grounding validation."""
    rag_patterns = [
        r'(vectorstore|vector_store|retriever)\.get_relevant_documents',
        r'(similarity_search|as_retriever)',
        r'(RetrievalQA|RAGChain|RAGPipeline)',
        r'(index\.query|pinecone\.query|weaviate\.query)',
    ]
    validation_patterns = [
        r'(ground|verify|validate|source|citation|score|threshold)',
    ]

    lines = source.splitlines()
    for i, line in enumerate(lines):
        for pattern in rag_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                surrounding = "\n".join(lines[max(0, i - 3):i + 8])
                has_validation = any(
                    re.search(vp, surrounding, re.IGNORECASE)
                    for vp in validation_patterns
                )
                if not has_validation:
                    findings.append(FindingData(
                        engine="ai_evals",
                        severity="MEDIUM",
                        category="ai_evals.rag_quality",
                        title="RAG pipeline lacks answer grounding validation",
                        description=(
                            f"RAG retrieval at line {i + 1} does not appear to validate "
                            f"answer grounding or retrieval relevance scores. Consider adding "
                            f"confidence thresholds and source citation checks."
                        ),
                        evidence={"snippet": line.strip()},
                        file_path="<source>",
                        line_number=i + 1,
                        pyramid_level=11,
                    ))
                break
