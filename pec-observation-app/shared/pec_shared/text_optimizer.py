"""Transcription text optimizer — reduces token count before LLM calls.

Applies four passes in order:
1. Strip common Portuguese filler/hesitation words
2. Collapse word-level immediate repetitions
3. Normalize whitespace and punctuation
4. Hard-cap at token budget (estimated 4 chars/token)
"""
import re
from typing import Optional

# Portuguese fillers that carry no semantic content
_FILLERS = re.compile(
    r"\b("
    r"né|né\?|né\.|"
    r"então|tá|ta bom|ta|"
    r"tipo assim|tipo|"
    r"ah+|é+h*|a+h+|a+hn+|"
    r"hmm+|hm+|uh+|uhm+|um+|"
    r"bom então|bom|"
    r"sabe|viu|olha|olhando|"
    r"assim assim|"
    r"quer dizer|ou seja"
    r")\b",
    re.IGNORECASE,
)

# Immediate word repetitions: "eu eu fui" → "eu fui"
_REPETITIONS = re.compile(r"\b(\w{2,})\s+\1\b", re.IGNORECASE)

# Multiple spaces / newlines → single space
_WHITESPACE = re.compile(r"[ \t\r\n]+")

# Repeated punctuation: ",,,," → ","  or "!!!" → "!"
_PUNCT = re.compile(r"([,;:.!?])\1+")

# Trailing commas before sentence end
_TRAILING_COMMA = re.compile(r",\s*([.!?])")

# Approximate chars-per-token for Portuguese (Llama tokenizer)
_CHARS_PER_TOKEN = 3.8


def _strip_fillers(text: str) -> str:
    cleaned = _FILLERS.sub(" ", text)
    # Remove dangling punctuation left by filler removal like " , " → " "
    cleaned = re.sub(r"\s+([,;])\s+([,;])", r" \2 ", cleaned)
    return cleaned


def _collapse_repetitions(text: str) -> str:
    # Run twice to handle triple repetitions
    for _ in range(2):
        text = _REPETITIONS.sub(r"\1", text)
    return text


def _normalize_whitespace_punct(text: str) -> str:
    text = _PUNCT.sub(r"\1", text)
    text = _TRAILING_COMMA.sub(r" \1", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def _apply_budget(text: str, max_tokens: int) -> str:
    char_limit = int(max_tokens * _CHARS_PER_TOKEN)
    if len(text) <= char_limit:
        return text
    # Truncate at last sentence boundary before limit
    cutoff = text.rfind(".", 0, char_limit)
    if cutoff < char_limit // 2:
        cutoff = char_limit
    return text[:cutoff].rstrip() + " [transcrição truncada por orçamento de tokens]"


def optimize(text: str, max_tokens: Optional[int] = 3500) -> str:
    """Return a token-reduced version of *text* suitable for LLM input.

    Args:
        text: Raw transcription text from Whisper.
        max_tokens: Hard budget. None disables truncation.

    Returns:
        Cleaned, compressed text.
    """
    text = _strip_fillers(text)
    text = _collapse_repetitions(text)
    text = _normalize_whitespace_punct(text)
    if max_tokens is not None:
        text = _apply_budget(text, max_tokens)
    return text


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (±15%)."""
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def optimization_report(original: str, optimized: str) -> dict:
    orig_tokens = estimate_tokens(original)
    opt_tokens = estimate_tokens(optimized)
    saved = orig_tokens - opt_tokens
    pct = round(saved / orig_tokens * 100, 1) if orig_tokens else 0.0
    return {
        "original_chars":  len(original),
        "optimized_chars": len(optimized),
        "estimated_tokens_before": orig_tokens,
        "estimated_tokens_after":  opt_tokens,
        "tokens_saved":  saved,
        "reduction_pct": pct,
    }
