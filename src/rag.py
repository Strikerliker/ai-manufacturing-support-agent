from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]+", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "why",
    "will",
    "with",
}


@dataclass(frozen=True)
class Passage:
    source: str
    section: str
    text: str
    score: float = 0.0


def tokenize(text: str) -> set[str]:
    return {
        token
        for match in TOKEN_RE.finditer(text)
        if (token := match.group(0).lower()) not in STOPWORDS
    }


def chunk_markdown(source: str, text: str) -> list[Passage]:
    passages: list[Passage] = []
    section = "Overview"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(line.strip() for line in buffer).strip()
        if body:
            passages.append(Passage(source=source, section=section, text=body))
        buffer = []

    for raw_line in text.splitlines():
        heading = HEADING_RE.match(raw_line.strip())
        if heading:
            flush()
            section = heading.group(1).strip()
        else:
            buffer.append(raw_line)
    flush()
    return passages


def score_passage(question: str, passage: Passage) -> float:
    query_terms = tokenize(question)
    if not query_terms:
        return 0.0

    title_terms = tokenize(passage.section)
    body_terms = tokenize(passage.text)
    overlap = query_terms & body_terms
    title_overlap = query_terms & title_terms

    if not overlap and not title_overlap:
        return 0.0

    coverage = len(overlap | title_overlap) / len(query_terms)
    density = len(overlap) / max(len(body_terms), 1)
    title_bonus = min(len(title_overlap) * 0.12, 0.36)
    return round((coverage * 0.78) + (density * 0.22) + title_bonus, 6)


def retrieve(
    question: str,
    passages: Iterable[Passage],
    *,
    top_k: int = 4,
    min_score: float = 0.08,
) -> list[Passage]:
    ranked: list[Passage] = []
    for passage in passages:
        score = score_passage(question, passage)
        if score >= min_score:
            ranked.append(Passage(passage.source, passage.section, passage.text, score))

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]


def format_context(passages: list[Passage]) -> str:
    blocks = []
    for index, passage in enumerate(passages, start=1):
        blocks.append(
            f"[SOURCE {index}] {passage.source} — {passage.section}\n{passage.text}"
        )
    return "\n\n".join(blocks)


def citations(passages: list[Passage]) -> list[dict[str, str | float]]:
    return [
        {
            "source": passage.source,
            "section": passage.section,
            "score": passage.score,
        }
        for passage in passages
    ]


ESCALATION_TERMS = {
    "ransomware",
    "malware",
    "breach",
    "compromised",
    "phishing",
    "safety",
    "injury",
    "emergency",
    "production down",
    "plant down",
    "privileged access",
    "administrator access",
    "data loss",
}


def requires_escalation(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    return any(term in normalized for term in ESCALATION_TERMS)


def fallback_answer() -> str:
    return (
        "I could not find an approved support procedure that confidently answers this question. "
        "Do not improvise a production or access-control change. Escalate to the appropriate "
        "manufacturing IT, ERP, security, or operations owner and provide the affected system, "
        "user, timestamp, error message, and business impact."
    )
