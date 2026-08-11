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
_DEFAULT_MODEL = "gemini-embedding-001"
_MODEL_DIMENSION = 3072         # gemini-embedding-001 fixed output dimension
_MODEL_VERSION = "v1"           # application-managed version tag
_PROVIDER_NAME = "gemini"

# Google API base URLs — both v1 and v1beta work for gemini-embedding-001.
# v1beta is listed first as it has wider model availability.
_REST_BASE_URLS = [
    "https://generativelanguage.googleapis.com/v1beta/models", # preferred for newer models
    "https://generativelanguage.googleapis.com/v1/models",     # v1 stable
]

# Bare model names tried in order. Update this list if the API key
# supports additional models. Only models confirmed available for this key
# are included. To check availability run:
#   python -c "import google.generativeai as g; g.configure(api_key='KEY'); [print(m.name) for m in g.list_models() if 'embedContent' in m.supported_generation_methods]"
_MODEL_BARE_NAMES = [
    "gemini-embedding-001",  # only confirmed-available embedding model
]


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

        # Try SDK first; fall back to REST on any non-fatal failure.
        # NOTE: EmbeddingRateLimitError and EmbeddingTimeoutError are always
        # re-raised immediately because they signal conditions where retrying
        # the REST path won't help (quota exhausted / network timeout).
        # EmbeddingProviderError (e.g. 404 NOT_FOUND model name mismatch) IS
        # allowed to fall through to the REST path so the fallback model chain
        # can be tried.
        if self._sdk_client is not None:
            try:
                return self._generate_via_sdk(texts)
            except (EmbeddingRateLimitError, EmbeddingTimeoutError):
                raise  # Fatal — don't try REST
            except EmbeddingConfigurationError:
                raise  # Bad API key — REST won't help either
            except Exception as exc:
                logger.warning(
                    "GeminiEmbeddingProvider — SDK call failed, falling back to REST: %s",
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

        Tries the bare model name first, then the prefixed form (models/<name>).
        The SDK processes one text at a time.
        """
        # Try bare name first, then models/<name> prefix
        model_candidates = [self._model]
        if not self._model.startswith("models/"):
            model_candidates.append(f"models/{self._model}")

        last_exc: Exception | None = None
        for candidate in model_candidates:
            try:
                vectors: list[list[float]] = []
                for text in texts:
                    result = self._sdk_client.models.embed_content(
                        model=candidate,
                        contents=text,
                    )
                    # google.genai SDK returns EmbedContentResponse:
                    # - .embedding (ContentEmbedding) with .values for single content
                    # - .embeddings (list[ContentEmbedding]) for batch
                    if hasattr(result, "embeddings") and result.embeddings:
                        embedding_obj = result.embeddings[0]
                    elif hasattr(result, "embedding") and result.embedding:
                        embedding_obj = result.embedding
                    else:
                        raise EmbeddingProviderError(
                            f"Unexpected SDK response structure for model={candidate!r}: "
                            f"no 'embedding' or 'embeddings' attribute found."
                        )
                    values = getattr(embedding_obj, "values", None)
                    if not values:
                        raise EmbeddingProviderError(
                            f"SDK returned empty values for model={candidate!r}."
                        )
                    vectors.append(list(values))
                logger.debug(
                    "GeminiEmbeddingProvider — SDK success: model=%s texts=%d",
                    candidate, len(texts),
                )
                return vectors
            except (EmbeddingProviderError, EmbeddingRateLimitError,
                    EmbeddingTimeoutError, EmbeddingConfigurationError):
                raise  # already typed — propagate immediately
            except Exception as exc:
                exc_str = str(exc).lower()
                if "404" in exc_str or "not found" in exc_str or "not_found" in exc_str:
                    logger.warning(
                        "GeminiEmbeddingProvider — SDK 404 for model=%s, trying next candidate",
                        candidate,
                    )
                    last_exc = exc
                    continue
                # Non-404 error — classify and raise immediately
                return self._classify_and_raise(exc)

        # All SDK candidates exhausted — fall through to REST
        return self._classify_and_raise(last_exc)

    # ── REST implementation ────────────────────────────────────────────────────

    def _generate_via_rest(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using the Gemini REST API (batchEmbedContents).

        Iterates over all combinations of (API version, model name) so that
        the request succeeds regardless of which version/model is available
        for the active API key:

            v1/text-embedding-004          ← preferred (stable)
            v1/embedding-001               ← stable legacy fallback
            v1beta/text-embedding-004      ← beta
            v1beta/embedding-001           ← beta legacy fallback
        """
        # Build primary bare name from configured model (strip any "models/" prefix)
        primary_bare = self._model.removeprefix("models/")

        # Ordered candidate list: (base_url, bare_model_name)
        candidates: list[tuple[str, str]] = []
        for base_url in _REST_BASE_URLS:
            for bare_name in _MODEL_BARE_NAMES:
                # Put the configured model name first within each API version
                if bare_name == primary_bare:
                    candidates.insert(
                        # insert at position = number of already-added entries for v1
                        sum(1 for c in candidates if _REST_BASE_URLS[0] in c[0]),
                        (base_url, bare_name),
                    )
                else:
                    candidates.append((base_url, bare_name))

        # Deduplicate while preserving order
        seen: set[tuple[str, str]] = set()
        ordered: list[tuple[str, str]] = []
        for entry in candidates:
            if entry not in seen:
                seen.add(entry)
                ordered.append(entry)

        last_err: Exception | None = None
        for base_url, bare_name in ordered:
            url = f"{base_url}/{bare_name}:batchEmbedContents?key={self._api_key}"
            model_field = f"models/{bare_name}"

            requests_payload = [
                {
                    "model": model_field,
                    "content": {"parts": [{"text": text}]},
                }
                for text in texts
            ]

            req = urllib.request.Request(
                url,
                data=json.dumps({"requests": requests_payload}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    vectors: list[list[float]] = [
                        emb.get("values", []) for emb in data.get("embeddings", [])
                    ]
                    label = f"{base_url.split('/v')[1].split('/')[0]}/{bare_name}"
                    if bare_name != primary_bare or "v1beta" in base_url:
                        logger.info(
                            "GeminiEmbeddingProvider — REST succeeded via %s", label
                        )
                    return vectors

            except urllib.error.HTTPError as err:
                if err.code == 404:
                    label = f"{base_url.split('/v')[1].split('/')[0]}/{bare_name}"
                    logger.warning(
                        "GeminiEmbeddingProvider — REST 404 for %s, trying next", label
                    )
                    last_err = err
                    continue
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

        tried = [(b.split("/v")[1].split("/")[0] + "/" + m) for b, m in ordered]
        raise EmbeddingProviderError(
            f"Gemini REST API returned 404 for all candidates: {tried}. "
            "Ensure the Generative Language API (embedding) is enabled for your "
            "API key at console.cloud.google.com, or set a different EMBEDDING_MODEL.",
            cause=last_err,
        ) from last_err

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
