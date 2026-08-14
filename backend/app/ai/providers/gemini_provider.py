"""
GeminiProvider — client provider for Google Gemini models.

Supports:
1. `google.generativeai` SDK (official stable Python SDK)
2. `google.genai` SDK
3. Standard library `urllib.request` REST API fallback with SSL context
"""
import json
import logging
import ssl
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# ── 1. Try google.generativeai (Official stable SDK) ──────────────────────────
GENERATIVEAI_SDK = False
try:
    import google.generativeai as genai_legacy  # type: ignore[import]
    GENERATIVEAI_SDK = True
except ImportError:
    genai_legacy = None  # type: ignore[assignment]

# ── 2. Try google.genai ───────────────────────────────────────────────────────
GENAI_SDK = False
try:
    import google.genai as genai  # type: ignore[import]
    from google.genai import types  # type: ignore[import]
    GENAI_SDK = True
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

from app.core.config import settings


class GeminiProvider:

    def __init__(self):
        if GENERATIVEAI_SDK and settings.GEMINI_API_KEY:
            try:
                genai_legacy.configure(api_key=settings.GEMINI_API_KEY)
                logger.info("Configured google.generativeai SDK successfully.")
            except Exception as exc:
                logger.warning("Failed to configure google.generativeai: %s", exc)

        if GENAI_SDK and settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.warning("Failed to initialize google.genai Client: %s", exc)
                self.client = None
        else:
            self.client = None

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        # Strategy 1: google.generativeai SDK (Most stable on Windows)
        if GENERATIVEAI_SDK and genai_legacy:
            try:
                model = genai_legacy.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=system_instruction,
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai_legacy.types.GenerationConfig(temperature=temperature),
                )
                if response and hasattr(response, "text") and response.text:
                    return response.text
            except Exception as exc:
                logger.warning("google.generativeai call failed, trying google.genai / REST fallback: %s", exc)

        # Strategy 2: google.genai SDK
        if GENAI_SDK and self.client:
            try:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction,
                )
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=config,
                )
                if response and hasattr(response, "text") and response.text:
                    return response.text
            except Exception as exc:
                logger.warning("google.genai call failed, trying REST fallback: %s", exc)

        # Strategy 3: Direct REST API via urllib.request (zero external dependency)
        return self._generate_via_rest(prompt, system_instruction, temperature)

    def _generate_via_rest(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured in settings.")

        # Clean model name (ensure no duplicate 'models/' prefix)
        model_name = settings.GEMINI_MODEL.removeprefix("models/")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SkillSwap-GeminiProvider/1.0",
            },
            method="POST",
        )

        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            logger.error("Gemini REST API error HTTP %d: %s", err.code, err_body)
            raise RuntimeError(f"Gemini API returned error {err.code}: {err_body}") from err
        except Exception as err:
            logger.error("Gemini REST API connection error: %s", err)
            raise RuntimeError(f"Failed to connect to Gemini API: {str(err)}") from err