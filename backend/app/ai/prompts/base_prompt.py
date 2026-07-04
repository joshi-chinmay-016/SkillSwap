from textwrap import dedent


def build_prompt(
    system_role: str,
    instructions: str,
    user_input: str
) -> str:

    return dedent(
        f"""
        {system_role}

        Instructions:

        {instructions}

        User Input:

        {user_input}
        """
    ).strip()