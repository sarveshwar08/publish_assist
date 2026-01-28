from zenml import step
from publish_assist.infra.llm import LlamaClient

@step
def call_llm(prompt: str) -> str:
    llm = LlamaClient()
    return llm.generate(prompt)
