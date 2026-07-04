import json


def parse_json_response(
    response: str
):

    response = response.strip()

    if response.startswith("```json"):

        response = response.replace(
            "```json",
            ""
        )

    if response.endswith("```"):

        response = response[:-3]

    response = response.strip()

    return json.loads(response)