from app.ai.schemas.mentor_recommendation import (
    MentorRecommendationRequest
)


def build_mentor_recommendation_prompt(

    request: MentorRecommendationRequest,

    mentors: list[dict]

) -> str:

    return f"""
A learner wants to learn:

{request.target_skill}

Available mentors:

{mentors}

Recommend the most suitable mentors.

For every mentor provide:

- mentor_name
- expertise
- reason

Return ONLY JSON.

Schema:

{{
    "mentors":[
        {{
            "mentor_name":"",
            "expertise":[],
            "reason":""
        }}
    ]
}}

No markdown.

Return JSON only.
"""