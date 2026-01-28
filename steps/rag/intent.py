from zenml import step

@step
def extract_intent(topic: str, platform: str, tone: str) -> dict:
    return {
        "topic": topic.strip(),
        "platform": platform,
        "tone": tone,
    }
