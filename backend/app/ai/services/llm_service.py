from app.ai.providers import GeminiProvider


class LLMService:

    def __init__(self):

        self.provider = GeminiProvider()

    def generate(

        self,

        prompt: str,

        system_prompt: str | None = None,

        temperature: float = 0.7

    ) -> str:

        return self.provider.generate_text(

            prompt=prompt,

            system_instruction=system_prompt,

            temperature=temperature

        )