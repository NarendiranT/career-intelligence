from __future__ import annotations

from typing import Any

# Groq on-demand gpt-oss TPM is 8000 and counts prompt + declared max_tokens.
ROUTER_MAX_TOKENS = 768
EXTRACTION_MAX_TOKENS = 1536
GENERATION_MAX_TOKENS_CAP = 1536
EXTRACT_DOCUMENT_CHARS = 14_000
TOPIC_ANSWER_CHARS = 8_000
CHUNK_PROMPT_LIMIT = 6
CHUNK_PROMPT_CHARS = 500


def truncate_text(text: str, max_chars: int) -> str:
    value = text or ""
    if max_chars <= 0 or len(value) <= max_chars:
        return value
    if max_chars == 1:
        return "…"
    return value[: max_chars - 1].rstrip() + "…"


def skill_label(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


def compact_profiles(profiles: dict[str, Any] | None) -> str:
    data = profiles or {}
    lines: list[str] = []
    for resume in data.get("resumes") or []:
        skills = ", ".join(label for item in (resume.get("skills") or [])[:24] if (label := skill_label(item)))
        lines.append(
            f"Resume {resume.get('filename') or resume.get('document_id')}: "
            f"name={resume.get('name') or ''}; headline={resume.get('headline') or ''}; "
            f"skills={skills}; summary={truncate_text(str(resume.get('summary') or ''), 400)}"
        )
        for exp in (resume.get("experience") or [])[:8]:
            highlights = "; ".join(str(item) for item in (exp.get("highlights") or [])[:4])
            lines.append(
                f"  - {exp.get('title') or ''} at {exp.get('company') or ''}: {truncate_text(highlights, 240)}"
            )
    for job in data.get("jobs") or []:
        skills = ", ".join(label for item in (job.get("skills") or [])[:24] if (label := skill_label(item)))
        reqs = "; ".join(str(item) for item in (job.get("requirements") or [])[:10])
        lines.append(
            f"Job {job.get('filename') or job.get('document_id')}: "
            f"{job.get('title') or ''} at {job.get('company') or ''}; skills={skills}; "
            f"requirements={truncate_text(reqs, 500)}"
        )
    return "\n".join(lines) if lines else "(none)"


def compact_chunks(chunks: list[dict[str, Any]] | None, *, limit: int = CHUNK_PROMPT_LIMIT, max_chars: int = CHUNK_PROMPT_CHARS) -> str:
    items = list(chunks or [])[:limit]
    if not items:
        return "(none)"
    blocks = []
    for item in items:
        filename = item.get("filename") or item.get("document_id") or "document"
        blocks.append(f"[{filename}]\n{truncate_text(str(item.get('content') or ''), max_chars)}")
    return "\n\n".join(blocks)


def compact_draft(draft: dict[str, Any] | None) -> str:
    data = draft or {}
    strengths = "; ".join(str(item) for item in (data.get("strengths") or [])[:8])
    gaps = "; ".join(str(item) for item in (data.get("gaps") or [])[:8])
    return (
        f"text={truncate_text(str(data.get('text') or ''), 1200)}\n"
        f"strengths={strengths}\n"
        f"gaps={gaps}"
    )


def compact_topic_context(context: dict[str, Any] | None) -> str:
    data = context if isinstance(context, dict) else {}
    answer = truncate_text(str(data.get("answer") or ""), 1200)
    return (
        f"resume_id={data.get('resume_id') or ''}\n"
        f"job_ids={data.get('job_ids') or []}\n"
        f"source answer excerpt:\n{answer or '(none)'}"
    )


def cap_generation_max_tokens(requested: int | None) -> int:
    value = int(requested) if requested else 1024
    return max(64, min(value, GENERATION_MAX_TOKENS_CAP))
