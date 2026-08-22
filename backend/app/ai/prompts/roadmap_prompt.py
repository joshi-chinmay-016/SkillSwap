from app.ai.schemas.roadmap import (
    RoadmapRequest
)


def build_roadmap_prompt(
    request: RoadmapRequest
) -> str:
    skills_str = ", ".join(request.current_skills) if request.current_skills else "Beginner (no previous skills listed)"

    return f"""
You are an expert technical mentor.

Generate a comprehensive, actionable learning roadmap.

Current Skills:
{skills_str}

Target Role:
{request.target_role}

Experience Level:
{request.experience_level}

Duration:
{request.duration_months} months

Requirements:
1. Divide the roadmap week by week ({request.duration_months * 4} weeks total).
2. Every week MUST have:
   - "week": integer week number
   - "topic": concise subject matter
   - "goal": clear learning objective for the week
   - "tasks": list of 2-3 specific hands-on tasks, each with "title", "description", and optional "resources" (list of URLs or search queries)
3. Focus heavily on practical projects and building real applications.
4. Return ONLY valid JSON following the schema below. No markdown backticks, no explanations.

Schema:
{{
  "title": "{request.target_role} Learning Roadmap",
  "weeks": [
    {{
      "week": 1,
      "topic": "Fundamentals",
      "goal": "Master core concepts",
      "tasks": [
        {{
          "title": "Set up development environment",
          "description": "Install required tools and build a hello-world project.",
          "resources": []
        }}
      ]
    }}
  ]
}}
"""