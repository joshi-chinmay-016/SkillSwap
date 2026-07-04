from app.ai.schemas.roadmap import (
    RoadmapRequest
)


def build_roadmap_prompt(
    request: RoadmapRequest
) -> str:

    return f"""
You are an expert software engineering mentor.

Generate a personalized learning roadmap.

Current Skills:
{", ".join(request.current_skills)}

Target Role:
{request.target_role}

Experience Level:
{request.experience_level}

Duration:
{request.duration_months} months

Requirements:

1. Divide the roadmap week by week.

2. Every week should have

- week
- topic
- goal

3. Focus on practical learning.

4. Include projects whenever appropriate.

5. Return ONLY valid JSON.

6. Do not repeat topics.

7. Keep the roadmap realistic for the specified duration.

8. Prefer hands-on learning over theory.

9. Ensure each week builds naturally on the previous one.

Use this schema exactly:

The response MUST strictly follow this schema:

{{
  "title": "...",
  "weeks": [
      {{
          "week": 1,
          "topic": "...",
          "goal": "..."
      }}
  ]
}}

The JSON must be parseable using Python's json.loads().

Do not include explanations.

Do not include markdown.

Do not include comments.

Do not wrap the JSON inside triple backticks.

Do not add markdown.

Do not wrap inside ```.

Return JSON only.
"""