"""
Day 71 Retrieval Package — Entry point.
"""

from app.retrieval.retrieval_exceptions import (
    InvalidRetrievalRequestError,
    MetadataResolutionError,
    QueryEmbeddingError,
    RetrievalError,
    RetrievalUnavailableError,
    VectorStoreSearchError,
)
from app.retrieval.retrieval_models import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
)
from app.retrieval.retriever import Retriever
from app.retrieval.faiss_retriever import FAISSRetriever
from app.retrieval.retrieval_service import RetrievalService

__all__ = [
    "InvalidRetrievalRequestError",
    "MetadataResolutionError",
    "QueryEmbeddingError",
    "RetrievalError",
    "RetrievalUnavailableError",
    "VectorStoreSearchError",
    "RetrievalRequest",
    "RetrievalResponse",
    "RetrievedChunk",
    "Retriever",
    "FAISSRetriever",
    "RetrievalService",
]
