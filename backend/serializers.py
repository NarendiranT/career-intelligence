from __future__ import annotations

from backend.api_schemas import DocumentOut
from backend.models import Document


def document_to_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        doc_type=doc.doc_type.value if doc.doc_type else None,
        status=doc.status.value,
        mime=doc.mime,
        size=doc.size,
        error_message=doc.error_message,
        created_at=doc.created_at,
    )
