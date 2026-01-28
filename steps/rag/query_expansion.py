from zenml import step

@step
def expand_query(topic: str) -> list[str]:
    return [
        topic,
        f"{topic} examples",
        f"{topic} key ideas",
    ]
