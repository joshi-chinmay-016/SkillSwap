import json
import re
import logging

logger = logging.getLogger("skillswap.json_parser")


def parse_json_response(response: str) -> dict | list:
    """
    Robustly extracts and parses JSON from LLM output.
    Handles markdown formatting, backticks, conversational preamble, and trailing text.
    """
    if not response or not isinstance(response, str):
        raise ValueError("Empty or invalid response received from LLM.")

    text = response.strip()

    # 1. Remove markdown code blocks if present
    if "```" in text:
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()

    # 2. Direct json.loads attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Find first outer '{' and matching '}' or '[' and ']'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket:last_bracket + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    logger.error(f"Failed to parse JSON from LLM response. Raw text: {response[:300]}...")
    raise ValueError(f"Could not parse valid JSON from AI response.")