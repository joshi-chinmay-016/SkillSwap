from app.ai.schemas.session_summary import (
    SessionSummaryRequest
)


def build_session_summary_prompt(
    request: SessionSummaryRequest
) -> str:

    return f"""
Summarize the following mentoring session.

Session Notes:

{request.session_notes}

Return ONLY valid JSON.

Schema:

{{
    "summary": "...",
    "key_points": [],
    "action_items": [],
    "recommended_resources": []
}}

Requirements:

1. Keep summary concise.

2. Extract major concepts.

3. Suggest practical action items.

4. Recommend useful learning resources.

5. Return JSON only.

Do not use markdown.

Do not wrap inside ```.

The response must be parseable using Python's json.loads().
"""