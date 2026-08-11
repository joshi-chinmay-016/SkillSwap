"""
Retrieval repository — batch PostgreSQL metadata resolution (Day 71).

Single batch query joining Embedding → Chunk → ParsedDocument → Document.
Avoids N+1 queries: all candidate metadata is fetched in one round trip.

Security:
    - Only non-sensitive metadata columns are fetched.
    - No raw vectors are loaded or logged.
    - No filesystem paths are returned.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class CandidateMetadata:
    """
    Flattened metadata for one retrieval candidate.

    Contains everything needed by FAISSRetriever to:
        - Authorize (embedding_user_id, document_user_id)
        - Filter lifecycle (embedding_status, chunk_status, document_status)
        - Construct RetrievedChunk (chunk_id, content, document_id, document_name)
    """

    embedding_id: str
    embedding_status: str
    embedding_user_id: int

    chunk_id: str
    chunk_status: str
    chunk_text: str
    parsed_document_id: str

    document_id: str
    document_name: str
    document_status: str
    document_user_id: int


def get_candidate_metadata_batch(
    db: Session,
    embedding_ids: list[str],
) -> dict[str, CandidateMetadata]:
    """
    Batch-resolve embedding IDs to full candidate metadata.

    Executes a single 4-table JOIN: embeddings → chunks → parsed_documents → documents.
    Returns only the columns needed by the retriever — no vector data loaded.

    Args:
        db            : Active SQLAlchemy session (read-only usage).
        embedding_ids : List of embedding UUID strings from FAISS ID resolution.

    Returns:
        Dict mapping embedding_id → CandidateMetadata.
        Missing embedding_ids (not in DB) are absent from the result dict —
        the retriever treats them as stale/orphaned vectors.
    """
    if not embedding_ids:
        return {}

    from app.models.chunk import Chunk
    from app.models.document import Document
    from app.models.embedding import Embedding
    from app.models.parsed_document import ParsedDocument

    rows = (
        db.query(
            Embedding.id.label("embedding_id"),
            Embedding.status.label("embedding_status"),
            Embedding.user_id.label("embedding_user_id"),
            Chunk.id.label("chunk_id"),
            Chunk.status.label("chunk_status"),
            Chunk.chunk_text.label("chunk_text"),
            Chunk.parsed_document_id.label("parsed_document_id"),
            Document.id.label("document_id"),
            Document.original_filename.label("document_name"),
            Document.status.label("document_status"),
            Document.user_id.label("document_user_id"),
        )
        .join(Chunk, Embedding.chunk_id == Chunk.id)
        .join(ParsedDocument, Chunk.parsed_document_id == ParsedDocument.id)
        .join(Document, ParsedDocument.document_id == Document.id)
        .filter(Embedding.id.in_(embedding_ids))
        .all()
    )

    result: dict[str, CandidateMetadata] = {}
    for row in rows:
        result[row.embedding_id] = CandidateMetadata(
            embedding_id=row.embedding_id,
            embedding_status=row.embedding_status,
            embedding_user_id=row.embedding_user_id,
            chunk_id=row.chunk_id,
            chunk_status=row.chunk_status,
            chunk_text=row.chunk_text,
            parsed_document_id=row.parsed_document_id,
            document_id=row.document_id,
            document_name=row.document_name or "",
            document_status=row.document_status,
            document_user_id=row.document_user_id,
        )

    if len(result) < len(embedding_ids):
        missing = len(embedding_ids) - len(result)
        logger.warning(
            "retrieval_repository — %d embedding_id(s) not found in DB "
            "(stale FAISS vectors). They will be skipped.",
            missing,
        )

    return result
