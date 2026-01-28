from zenml import pipeline

from steps.rag.intent import extract_intent
from steps.rag.query_expansion import expand_query
from steps.rag.retrieval import retrieve_chunks
from steps.rag.rerank import rerank_chunks
from steps.rag.context import build_context
from steps.rag.prompt import build_prompt
from steps.rag.llm import call_llm

@pipeline
def generate_content_pipeline(
    dataset_id: str,
    topic: str,
    platform: str,
    tone: str,
    use_web: bool = False, #TODO P2: implement separate call to web 
):
    intent = extract_intent(topic, platform, tone)
    queries = expand_query(topic)

    style_raw = retrieve_chunks(dataset_id, queries, platform, kind="style")
    content_raw = retrieve_chunks(dataset_id, queries, platform, kind="content")

    style = rerank_chunks(topic, style_raw, top_n=5)
    content = rerank_chunks(topic, content_raw, top_n=8)

    context = build_context(style, content)
    prompt = build_prompt(intent, context)

    output = call_llm(prompt)

    return {
        "output": output,
        "context": context,
        "style_raw": style_raw,
        "content_raw": content_raw,
    }


def run_generate_content(
    dataset_id: str,
    topic: str,
    platform: str,
    tone: str,
    use_web: bool = False,
):

    return generate_content_pipeline(
        dataset_id=dataset_id,
        topic=topic,
        platform=platform,
        tone=tone,
        use_web=use_web,
    )
