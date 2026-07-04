from app.ai.schemas.skill_gap import (
    SkillGapRequest
)


def build_skill_gap_prompt(
    request: SkillGapRequest
) -> str:

    return f"""
You are an expert software engineering career mentor.

Analyze the user's skills against the target role.

Current Skills:
{", ".join(request.current_skills)}

Target Role:
{request.target_role}

Return ONLY valid JSON.

Use this schema exactly:

{{
    "target_role": "...",
    "matched_skills": [],
    "missing_skills": [],
    "recommendations": []
}}

Requirements:

1. Compare current skills with industry expectations.

2. Identify missing technical skills.

3. Do not include duplicate skills.

4. Give practical learning recommendations.

5. Return JSON only.

Do not use markdown.

Do not wrap inside ```.

The JSON must be parseable using Python's json.loads().
"""