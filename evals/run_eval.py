from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.indexing.graph import indexing_graph
from agent.rag.graph import rag_graph
from backend.db import session_scope
from backend.models import Document, DocumentStatus, DocType

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENSET_DIR = Path(__file__).resolve().parent / "goldensets"


def load_goldenset(name: str) -> list[dict[str, Any]]:
    path = GOLDENSET_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_fixture(fixture: str, dest_dir: Path) -> Path:
    src = REPO_ROOT / fixture
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def index_document(*, user_id: uuid.UUID, dest: Path, doc_type: str) -> dict[str, Any]:
    document_id = uuid.uuid4()
    with session_scope() as db:
        db.add(
            Document(
                id=document_id,
                user_id=user_id,
                doc_type=DocType(doc_type),
                filename=dest.name,
                storage_path=str(dest),
                status=DocumentStatus.uploaded,
                mime="text/plain",
                size=dest.stat().st_size,
            )
        )
    result = indexing_graph.invoke({"user_id": str(user_id), "document_id": str(document_id)})
    result["document_id"] = str(document_id)
    return result


@dataclass
class EvalCorpus:
    user_id: uuid.UUID
    resume_id: str
    job_id: str
    indexing: dict[str, dict[str, Any]]


def build_eval_corpus(user_id: uuid.UUID, dest_dir: Path) -> EvalCorpus:
    goldens = load_goldenset("indexing.json")
    indexing: dict[str, dict[str, Any]] = {}
    resume_id = ""
    job_id = ""
    for golden in goldens:
        dest = _copy_fixture(golden["fixture"], dest_dir)
        result = index_document(user_id=user_id, dest=dest, doc_type=golden["doc_type"])
        if result.get("error"):
            raise RuntimeError(f"indexing failed for {golden['id']}: {result['error']}")
        indexing[golden["id"]] = result
        if golden["doc_type"] == "resume":
            resume_id = result["document_id"]
        else:
            job_id = result["document_id"]
    return EvalCorpus(user_id=user_id, resume_id=resume_id, job_id=job_id, indexing=indexing)


def profile_output(result: dict[str, Any]) -> str:
    return json.dumps(result.get("profile") or {}, default=str)


def run_rag_case(corpus: EvalCorpus, golden: dict[str, Any]) -> dict[str, Any]:
    job_ids = [corpus.job_id] if golden.get("include_job") and corpus.job_id else []
    result = rag_graph.invoke(
        {
            "user_id": str(corpus.user_id),
            "question": golden["input"],
            "resume_id": corpus.resume_id,
            "job_ids": job_ids,
        }
    )
    answer = result.get("answer") or {}
    text = answer.get("text", "") if isinstance(answer, dict) else str(answer)
    chunks = [item.get("content", "") for item in result.get("chunks") or [] if item.get("content")]
    if not chunks:
        profiles = result.get("profiles") or {}
        chunks = [json.dumps(profiles, default=str)] if profiles else [""]
    return {"text": text, "retrieval_context": chunks, "raw": result}


def keyword_hit(blob: str, keywords: list[str]) -> bool:
    lowered = blob.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
