from groq import Groq
from publish_assist.settings import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)


class LlamaClient:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.model = model
        self.system_instruction = (
            "You are an AI writing assistant that generates original content. "
            "You may use reference material for inspiration, but you should not copy or "
            "closely imitate any provided text."
        )

    def generate(self, prompt: str) -> str:
        response = groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return (response.choices[0].message.content or "").strip()