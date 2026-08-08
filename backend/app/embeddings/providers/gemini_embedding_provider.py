"""
GeminiEmbeddingProvider — Google Gemini embedding implementation (Day 69 Part A1).

Uses the Google Gemini text-embedding-004 model to generate 768-dimensional
embedding vectors. This is the same credential infrastructure used by the
existing GeminiProvider (for text generation) — no new API keys required.

Supports two call paths:
    1. google.genai SDK (preferred)
    2. Standard library urllib.request REST fallback (zero-dependency)

Configuration (all from environment / pydantic Settings):
    EMBEDDING_PROVIDER=gemini
    EMBEDDING_MODEL=text-embedding-004
    EMBEDDING_API_KEY=<same as GEMINI_API_KEY by default>
    EMBEDDING_TIMEOUT=30

Provider limits (for reference — enforce in EmbeddingService, not here):
    - Batch size: up to 100 texts per request (we default to 32 via EMBEDDING_BATCH_SIZE)
    - Dimension: 768 (text-embedding-004)
    - Input token limit: ~2048 tokens per text

Security:
    - API key is read from settings; never hardcoded.
    - API key is never logged.
    - Request bodies (containing chunk text) are never logged.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from app.embeddings.embedding_provider import EmbeddingProvider
from app.exceptions.embedding_exceptions import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
)

logger = logging.getLogger(__name__)

# ── Optional google.genai SDK ─────────────────────────────────────────────────
_GENAI_SDK_AVAILABLE = False
try:
    import google.genai as genai  # type: ignore[import]
    from google.genai import types as genai_types  # type: ignore[import]
    _GENAI_SDK_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]


# ── Model constants ────────────────────────────────────────────────────────────
_DEFAULT_MODEL = "text-embedding-004"
_MODEL_DIMENSION = 768          # text-embedding-004 fixed output dimension
_MODEL_VERSION = "v1"           # application-managed version tag
_PROVIDER_NAME = "gemini"
_REST_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider backed by Google Gemini text-embedding-004.

    Dimension: 768 (fixed for text-embedding-004).

    This class is responsible ONLY for making API calls and returning raw
    vectors. Retry logic, rate-limit handling, batching strategy, and
    persistence belong to EmbeddingService.

    Raises:
        EmbeddingConfigurationError : EMBEDDING_API_KEY / GEMINI_API_KEY not set.
        EmbeddingRateLimitError     : HTTP 429 from API.
        EmbeddingTimeoutError       : Request timed out.
        EmbeddingProviderError      : Any other provider-side failure.
    """

    def __init__(self) -> None:
        from app.core.config import settings

        # Prefer EMBEDDING_API_KEY; fall back to GEMINI_API_KEY
        self._api_key: str = (
            getattr(settings, "EMBEDDING_API_KEY", None)
            or getattr(settings, "GEMINI_API_KEY", None)
            or ""
        )
        self._model: str = getattr(settings, "EMBEDDING_MODEL", _DEFAULT_MODEL)
        self._timeout: int = getattr(settings, "EMBEDDING_TIMEOUT", 30)

        if not self._api_key:
            raise EmbeddingConfigurationError(
                "No embedding API key configured. "
                "Set EMBEDDING_API_KEY or GEMINI_API_KEY in environment."
            )

        # Try to initialise the google.genai SDK client
        self._sdk_client: Any = None
        if _GENAI_SDK_AVAILABLE:
            try:
                self._sdk_client = genai.Client(api_key=self._api_key)
                logger.debug(
                    "GeminiEmbeddingProvider — using google.genai SDK, model=%s",
                    self._model,
                )
            except Exception as exc:
                logger.warning(
                    "GeminiEmbeddingProvider — google.genai SDK init failed, "
                    "falling back to REST: %s",
                    exc,
                )
                self._sdk_client = None
        else:
            logger.debug(
                "GeminiEmbeddingProvider — google.genai not installed, using REST fallback."
            )

    # ── Public interface ───────────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate a single embedding for the given text.

        Internally calls generate_embeddings([text]) for code reuse.
        """
        if not text or not text.strip():
            raise EmbeddingProviderError(
                "Cannot generate embedding for empty or whitespace-only text."
            )
        results = self.generate_embeddings([text])
        return results[0]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts in a single API call.

        Args:
            texts: Non-empty list of non-empty strings.

        Returns:
            List of float vectors in the same order as texts.

        Raises:
            EmbeddingConfigurationError : API key missing.
            EmbeddingRateLimitError     : HTTP 429.
            EmbeddingTimeoutError       : Timeout.
            EmbeddingProviderError      : Other failure.
        """
        if not texts:
            return []

        # Try SDK first, then REST
        if self._sdk_client is not None:
            try:
                return self._generate_via_sdk(texts)
            except (EmbeddingRateLimitError, EmbeddingTimeoutError, EmbeddingProviderError):
                raise  # Don't swallow classified exceptions
            except Exception as exc:
                logger.warning(
                    "GeminiEmbeddingProvider — SDK call failed, trying REST fallback: %s",
                    exc,
                )

        return self._generate_via_rest(texts)

    def get_dimension(self) -> int:
        return _MODEL_DIMENSION

    def get_model_name(self) -> str:
        return self._model

    def get_model_version(self) -> str:
        return _MODEL_VERSION

    @property
    def provider_name(self) -> str:
        return _PROVIDER_NAME

    # ── SDK implementation ─────────────────────────────────────────────────────

    def _generate_via_sdk(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using the google.genai SDK.

        The SDK accepts a list of contents; we process them individually
        since the v1 SDK's embed_content may accept only one at a time.
        We process batch by iterating and collecting results.
        """
        try:
            vectors: list[list[float]] = []
            for text in texts:
                result = self._sdk_client.models.embed_content(
                    model=self._model,
                    contents=text,
                )
                # SDK returns an EmbedContentResponse with .embeddings
                embedding_obj = result.embeddings[0]
                vectors.append(list(embedding_obj.values))
            return vectors
        except Exception as exc:
            return self._classify_and_raise(exc)

    # ── REST implementation ────────────────────────────────────────────────────

    def _generate_via_rest(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using the Gemini REST API (batchEmbedContents).

        REST endpoint: POST /v1beta/models/{model}:batchEmbedContents

        This endpoint accepts up to 100 contents per request.
        """
        url = (
            f"{_REST_BASE_URL}/{self._model}:batchEmbedContents"
            f"?key={self._api_key}"
        )

        # Build request payload
        requests_payload = [
            {
                "model": f"models/{self._model}",
                "content": {"parts": [{"text": text}]},
            }
            for text in texts
        ]
        payload = {"requests": requests_payload}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings_data = data.get("embeddings", [])
                vectors: list[list[float]] = []
                for emb in embeddings_data:
                    vectors.append(emb.get("values", []))
                return vectors

        except urllib.error.HTTPError as err:
            self._handle_http_error(err)
        except TimeoutError as exc:
            raise EmbeddingTimeoutError(
                f"Gemini embedding REST call timed out after {self._timeout}s.",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise EmbeddingProviderError(
                f"Gemini embedding REST call failed: {exc}",
                cause=exc,
            ) from exc

    # ── Error handling ─────────────────────────────────────────────────────────

    def _handle_http_error(self, err: urllib.error.HTTPError) -> None:
        """Classify HTTP errors into typed embedding exceptions."""
        # Read body for logging (no sensitive content — this is a response, not a request)
        try:
            body = err.read().decode("utf-8", errors="ignore")
        except Exception:
            body = "<unreadable>"

        if err.code == 429:
            logger.warning(
                "GeminiEmbeddingProvider — rate limit hit (HTTP 429). model=%s",
                self._model,
            )
            raise EmbeddingRateLimitError(
                f"Gemini API rate limit exceeded (HTTP 429). model={self._model}",
                cause=err,
            ) from err

        if err.code in (500, 502, 503, 504):
            logger.warning(
                "GeminiEmbeddingProvider — provider server error HTTP %d. model=%s",
                err.code,
                self._model,
            )
            raise EmbeddingProviderError(
                f"Gemini API server error HTTP {err.code}. model={self._model}",
                cause=err,
            ) from err

        if err.code == 401:
            raise EmbeddingConfigurationError(
                "Gemini API returned HTTP 401 Unauthorized. "
                "Check EMBEDDING_API_KEY / GEMINI_API_KEY.",
                cause=err,
            ) from err

        logger.error(
            "GeminiEmbeddingProvider — unexpected HTTP %d. model=%s",
            err.code,
            self._model,
        )
        raise EmbeddingProviderError(
            f"Gemini API returned HTTP {err.code}. model={self._model}",
            cause=err,
        ) from err

    def _classify_and_raise(self, exc: Exception) -> list[list[float]]:
        """Map an SDK exception to a typed embedding exception and re-raise."""
        exc_str = str(exc).lower()
        if "quota" in exc_str or "rate" in exc_str or "429" in exc_str:
            raise EmbeddingRateLimitError(
                f"Gemini SDK rate limit: {exc}", cause=exc
            ) from exc
        if "timeout" in exc_str or "deadline" in exc_str:
            raise EmbeddingTimeoutError(
                f"Gemini SDK timeout: {exc}", cause=exc
            ) from exc
        raise EmbeddingProviderError(
            f"Gemini SDK error: {exc}", cause=exc
        ) from exc
